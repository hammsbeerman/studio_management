from dataclasses import dataclass, field
from django.apps import apps
from django.db import transaction
from django.db.models import Exists, OuterRef, Max
from collections import Counter
from django.utils import timezone
from typing import Optional, Iterable, List
from inventory.models import InventoryMaster, InventoryLedger, VendorItemDetail, RetailWorkorderItem, SetPrice, Inventory
from finance.models import InvoiceItem
from krueger.models import KruegerJobDetail, WideFormat
from pricesheet.models import PriceSheet, WideFormatPriceSheet
from retail.models import RetailSaleLine
from onlinestore.models import StoreItemDetails, StoreItemDetailHistory




@dataclass
class ItemUsage:
    item_id: int
    has_ledger: bool
    used_in_retail: bool
    used_in_retail_workorders: bool
    used_in_online_store: bool
    safe_to_archive: bool
    reasons_blocked: List[str]


def classify_item_usage(item: InventoryMaster) -> ItemUsage:
    reasons: List[str] = []

    has_ledger = InventoryLedger.objects.filter(inventory_item=item).exists()
    if has_ledger:
        reasons.append("Ledger history")

    used_in_retail = item.retail_lines.exists()
    if used_in_retail:
        reasons.append("Used in retail sales")

    used_in_retail_workorders = item.retail_workorder_items.exists()
    if used_in_retail_workorders:
        reasons.append("Used in retail workorders")

    used_in_online_store = (
        StoreItemDetails.objects.filter(item=item).exists()
        or StoreItemDetailHistory.objects.filter(item=item).exists()
    )
    if used_in_online_store:
        reasons.append("Online store item")

    # ✅ AP invoices
    InvoiceItem = apps.get_model("finance", "InvoiceItem")
    if InvoiceItem.objects.filter(internal_part_number=item).exists():
        reasons.append("Used in AP invoices")

    # ✅ Legacy Inventory mapping (lots of print/job tables point to this)
    LegacyInventory = apps.get_model("inventory", "Inventory")
    legacy_qs = LegacyInventory.objects.filter(internal_part_number=item)

    # If you don't even have a legacy row, most downstream checks can be skipped
    if legacy_qs.exists():
        # ✅ Print jobs / production materials
        KruegerJobDetail = apps.get_model("krueger", "KruegerJobDetail")

        if KruegerJobDetail.objects.filter(paper_stock__internal_part_number=item).exists():
            reasons.append("Used as paper_stock in jobs")

        if KruegerJobDetail.objects.filter(packaging__internal_part_number=item).exists():
            reasons.append("Used as packaging in jobs")

        # ✅ Optional: pricesheets / setprice (only if apps exist)
        try:
            PriceSheet = apps.get_model("pricesheet", "PriceSheet")
            if PriceSheet.objects.filter(paper_stock__internal_part_number=item).exists():
                reasons.append("Used as paper_stock in pricesheets")
            if PriceSheet.objects.filter(packaging__internal_part_number=item).exists():
                reasons.append("Used as packaging in pricesheets")
        except LookupError:
            pass

        try:
            SetPrice = apps.get_model("inventory", "SetPrice")
            if SetPrice.objects.filter(paper_stock__internal_part_number=item).exists():
                reasons.append("Used in SetPrice")
        except LookupError:
            pass

    safe_to_archive = len(reasons) == 0

    return ItemUsage(
        item_id=item.id,
        has_ledger=has_ledger,
        used_in_retail=used_in_retail,
        used_in_retail_workorders=used_in_retail_workorders,
        used_in_online_store=used_in_online_store,
        safe_to_archive=safe_to_archive,
        reasons_blocked=reasons,
    )

@dataclass
class BulkArchiveResult:
    scanned: int = 0
    eligible: int = 0
    archived: int = 0
    blocked: int = 0
    errors: int = 0
    blocked_reasons: dict = field(default_factory=dict)
    examples: dict = field(default_factory=lambda: {"archived": [], "blocked": [], "errors": []})

def bulk_archive_unused_items(
    *,
    only_active: bool,
    vendor_id: Optional[int],
    name_contains: str,
    include_non_inventory: bool,
    limit: int,
    selected_item_ids: Optional[List[int]],
    dry_run: bool,
) -> BulkArchiveResult:
    res = BulkArchiveResult()

    # Build queryset same way your bulk_apply_to_queryset does
    qs = InventoryMaster.objects.all()

    if only_active:
        qs = qs.filter(active=True) if hasattr(InventoryMaster, "active") else qs
    if not include_non_inventory:
        qs = qs.filter(non_inventory=False)
    if vendor_id:
        qs = qs.filter(primary_vendor_id=vendor_id)
    if name_contains:
        qs = qs.filter(name__icontains=name_contains)

    if selected_item_ids:
        qs = qs.filter(id__in=selected_item_ids)

    qs = qs.order_by("id")[:limit]

    reason_counts = Counter()

    with transaction.atomic():
        for item in qs:
            res.scanned += 1
            try:
                usage = classify_item_usage(item)
                if usage.safe_to_archive:
                    res.eligible += 1
                    if not dry_run:
                        # Pick your “archive” policy:
                        # safest is non_inventory=True OR active=False (whichever you use)
                        item.non_inventory = True
                        item.save(update_fields=["non_inventory"])
                        res.archived += 1
                        if len(res.examples["archived"]) < 10:
                            res.examples["archived"].append(f"{item.id}:{item.name}")
                else:
                    res.blocked += 1
                    for r in usage.reasons_blocked:
                        reason_counts[r] += 1
                    if len(res.examples["blocked"]) < 10:
                        res.examples["blocked"].append(f"{item.id}:{item.name} ({', '.join(usage.reasons_blocked)})")
            except Exception as e:
                res.errors += 1
                if len(res.examples["errors"]) < 10:
                    res.examples["errors"].append(f"{item.id}:{item.name} ({e})")

        if dry_run:
            # don’t change anything
            transaction.set_rollback(True)

    res.blocked_reasons = dict(reason_counts)
    return res