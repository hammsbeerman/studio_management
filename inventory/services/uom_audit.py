from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, List, Optional, Dict
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q

from inventory.models import InventoryMaster, InventoryQtyVariations, InventoryLedger
from controls.models import Measurement  # ✅ measurement lives in controls


# -------------------------------------------------------------------
# Canonical Measurement Alias Map
# -------------------------------------------------------------------
# Canonical: "Each" (id=16), aliases include "Ea" (id=1)
# Canonical: "Sht"  (id=4), aliases include "Sheet", "Sheets"
CANONICAL_MEASUREMENT_ALIASES: Dict[str, List[str]] = {
    "Each": ["Ea"],
    "Sht": ["Sheet", "Sheets"],
}


# -------------------------
# Audit types
# -------------------------

@dataclass
class UomIssue:
    code: str
    message: str


@dataclass
class UomAuditRow:
    item: InventoryMaster
    base: Optional[InventoryQtyVariations]
    default_sell: Optional[InventoryQtyVariations]
    default_receive: Optional[InventoryQtyVariations]
    issues: List[UomIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


@dataclass
class UomAuditSummary:
    matched: int = 0
    ok: int = 0
    with_issues: int = 0
    by_issue_code: Dict[str, int] = field(default_factory=dict)


@dataclass
class UomAuditResult:
    rows: List[UomAuditRow]
    summary: UomAuditSummary


# -------------------------
# Query builder
# -------------------------

def build_items_for_uom_audit(
    *,
    only_active: bool = True,
    vendor_id: Optional[int] = None,
    name_contains: str = "",
    retail_only: bool = False,
    supplies_only: bool = False,
    include_non_inventory: bool = False,
) -> "Iterable[InventoryMaster]":
    qs = InventoryMaster.objects.all()

    if only_active:
        qs = qs.filter(active=True)

    if vendor_id:
        qs = qs.filter(primary_vendor_id=vendor_id)

    if name_contains:
        qs = qs.filter(Q(name__icontains=name_contains) | Q(description__icontains=name_contains))

    if retail_only:
        qs = qs.filter(retail=True)

    if supplies_only:
        qs = qs.filter(supplies=True)

    if not include_non_inventory:
        # If your non_inventory means "doesn't affect stock", skip by default
        qs = qs.exclude(non_inventory=True)

    qs = qs.prefetch_related(
        Prefetch(
            "variations",
            queryset=InventoryQtyVariations.objects.select_related("variation").all(),
        )
    ).order_by("name")

    return qs


# -------------------------
# Audit logic
# -------------------------

def audit_uom_for_items(items: Iterable[InventoryMaster]) -> UomAuditResult:
    rows: List[UomAuditRow] = []
    summary = UomAuditSummary()

    for item in items:
        summary.matched += 1

        vars_list: List[InventoryQtyVariations] = list(getattr(item, "variations").all())

        base_any = [v for v in vars_list if v.is_base_unit]
        default_sell_any = [v for v in vars_list if v.is_default_sell_uom]
        default_receive_any = [v for v in vars_list if v.is_default_receive_uom]

        # pick "single" active base/defaults (else None)
        base_active = [v for v in base_any if v.active]
        sell_active = [v for v in default_sell_any if v.active]
        recv_active = [v for v in default_receive_any if v.active]

        base = base_active[0] if len(base_active) == 1 else None
        default_sell = sell_active[0] if len(sell_active) == 1 else None
        default_receive = recv_active[0] if len(recv_active) == 1 else None

        issues: List[UomIssue] = []

        # ------------------------------------------------------------
        # Alias/canonical detection (THIS is where name_to_ids goes)
        # ------------------------------------------------------------
        # Build a map: measurement_name -> set(measurement_id)
        name_to_ids: Dict[str, set] = {}
        for v in vars_list:
            if v.variation_id:
                n = (v.variation.name or "").strip()
                if n:
                    name_to_ids.setdefault(n, set()).add(v.variation_id)

        # If an item uses both canonical + any aliases, flag it
        for canonical, aliases in CANONICAL_MEASUREMENT_ALIASES.items():
            used_names = []
            if canonical in name_to_ids:
                used_names.append(canonical)
            for a in aliases:
                if a in name_to_ids:
                    used_names.append(a)

            if len(used_names) > 1:
                issues.append(
                    UomIssue(
                        "MEASUREMENT_ALIAS_MIXED",
                        f"Uses canonical/alias measurements for '{canonical}': {', '.join(used_names)}",
                    )
                )

        # No variations at all
        if not vars_list:
            issues.append(UomIssue("NO_VARIATIONS", "No UOM variations exist for this item."))

        # Base unit checks
        if not base_any:
            issues.append(UomIssue("MISSING_BASE", "Missing base unit."))
        elif len(base_any) > 1:
            issues.append(UomIssue("MULTIPLE_BASE", "Multiple base units flagged."))

        # Validate base candidates
        for v in base_any:
            if not v.active:
                issues.append(UomIssue("INACTIVE_BASE", "Base unit is inactive."))
            if v.variation_qty is None or Decimal(v.variation_qty) != Decimal("1.0000"):
                issues.append(UomIssue("BASE_QTY_NOT_1", "Base unit must have variation_qty = 1.0000."))

        # Default sell checks (only if retail)
        if item.retail:
            if not default_sell_any:
                issues.append(UomIssue("MISSING_DEFAULT_SELL", "Retail item missing default sell UOM."))
            elif len(default_sell_any) > 1:
                issues.append(UomIssue("MULTIPLE_DEFAULT_SELL", "Multiple default sell UOMs flagged."))

        # Default receive checks (only if supplies)
        if item.supplies:
            if not default_receive_any:
                issues.append(UomIssue("MISSING_DEFAULT_RECEIVE", "Supplies item missing default receive UOM."))
            elif len(default_receive_any) > 1:
                issues.append(UomIssue("MULTIPLE_DEFAULT_RECEIVE", "Multiple default receive UOMs flagged."))

        # Variation qty sanity
        for v in vars_list:
            if v.variation_qty is None:
                issues.append(UomIssue("VAR_QTY_NULL", "A variation has NULL variation_qty."))
            else:
                try:
                    if Decimal(v.variation_qty) <= 0:
                        issues.append(UomIssue("VAR_QTY_NONPOSITIVE", "A variation has variation_qty <= 0."))
                except Exception:
                    issues.append(UomIssue("VAR_QTY_BAD", "A variation has a non-numeric variation_qty."))

        row = UomAuditRow(
            item=item,
            base=base,
            default_sell=default_sell,
            default_receive=default_receive,
            issues=issues,
        )

        if row.ok:
            summary.ok += 1
        else:
            summary.with_issues += 1
            for issue in row.issues:
                summary.by_issue_code[issue.code] = summary.by_issue_code.get(issue.code, 0) + 1

        rows.append(row)

    return UomAuditResult(rows=rows, summary=summary)


# -------------------------
# Fix helpers (safe defaults)
# -------------------------

@transaction.atomic
def ensure_base_uom(
    *,
    item: InventoryMaster,
    measurement: Measurement,
    activate: bool = True,
    also_set_default_sell: bool = False,
    also_set_default_receive: bool = False,
) -> InventoryQtyVariations:
    existing_bases = InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True)
    if existing_bases.count() > 1:
        raise ValueError(f"Item {item.pk} has multiple base units; resolve explicitly.")

    base = existing_bases.first()
    if base:
        changed = False
        if base.variation_id != measurement.id:
            base.variation = measurement
            changed = True
        if base.variation_qty != Decimal("1.0000"):
            base.variation_qty = Decimal("1.0000")
            changed = True
        if activate and not base.active:
            base.active = True
            changed = True
        if not base.is_base_unit:
            base.is_base_unit = True
            changed = True
        if changed:
            base.save()
    else:
        base = InventoryQtyVariations.objects.create(
            inventory=item,
            variation=measurement,
            variation_qty=Decimal("1.0000"),
            active=activate,
            is_base_unit=True,
        )

    if also_set_default_sell:
        set_default_sell_uom(item=item, uom=base)

    if also_set_default_receive:
        set_default_receive_uom(item=item, uom=base)

    return base


@transaction.atomic
def set_default_sell_uom(*, item: InventoryMaster, uom: InventoryQtyVariations) -> None:
    InventoryQtyVariations.objects.filter(inventory=item, is_default_sell_uom=True).exclude(pk=uom.pk).update(
        is_default_sell_uom=False
    )
    if not uom.is_default_sell_uom:
        uom.is_default_sell_uom = True
        uom.save(update_fields=["is_default_sell_uom"])


@transaction.atomic
def set_default_receive_uom(*, item: InventoryMaster, uom: InventoryQtyVariations) -> None:
    InventoryQtyVariations.objects.filter(inventory=item, is_default_receive_uom=True).exclude(pk=uom.pk).update(
        is_default_receive_uom=False
    )
    if not uom.is_default_receive_uom:
        uom.is_default_receive_uom = True
        uom.save(update_fields=["is_default_receive_uom"])


# -------------------------
# Base unit change (guardrails)
# -------------------------

@transaction.atomic
def set_base_uom(
    *,
    item: InventoryMaster,
    new_measurement: Measurement,
    conversion_factor_oldbase_to_newbase: Optional[Decimal] = None,
    rescale_existing_variations: bool = False,
    rescale_ledger_entries: bool = False,
) -> InventoryQtyVariations:
    current_bases = list(
        InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True)
    )
    if len(current_bases) > 1:
        raise ValueError(f"Item {item.pk} has multiple base units; resolve duplicates first.")

    has_ledger = InventoryLedger.objects.filter(inventory_item=item).exists()
    if has_ledger:
        if not rescale_ledger_entries:
            raise ValueError(
                f"Item {item.pk} has ledger history; cannot change base without rescaling ledger."
            )
        if conversion_factor_oldbase_to_newbase is None:
            raise ValueError("conversion_factor_oldbase_to_newbase is required to rescale ledger.")

    target = InventoryQtyVariations.objects.filter(
        inventory=item,
        variation=new_measurement,
        variation_qty=Decimal("1.0000"),
    ).first()

    if not target:
        target = InventoryQtyVariations.objects.create(
            inventory=item,
            variation=new_measurement,
            variation_qty=Decimal("1.0000"),
            active=True,
        )

    InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True).exclude(pk=target.pk).update(is_base_unit=False)

    if not target.is_base_unit:
        target.is_base_unit = True
        target.active = True
        target.save(update_fields=["is_base_unit", "active"])

    if rescale_existing_variations:
        if conversion_factor_oldbase_to_newbase is None:
            raise ValueError("conversion_factor_oldbase_to_newbase is required to rescale variations.")
        factor = Decimal(conversion_factor_oldbase_to_newbase)
        if factor <= 0:
            raise ValueError("conversion_factor_oldbase_to_newbase must be > 0")

        others = InventoryQtyVariations.objects.filter(inventory=item).exclude(pk=target.pk)
        to_update = []
        for v in others:
            if v.variation_qty is None:
                continue
            try:
                old = Decimal(v.variation_qty)
            except Exception:
                continue
            new_qty = (old / factor).quantize(Decimal("0.0001"))
            if new_qty <= 0:
                continue
            if v.variation_qty != new_qty:
                v.variation_qty = new_qty
                to_update.append(v)
        if to_update:
            InventoryQtyVariations.objects.bulk_update(to_update, ["variation_qty"])

    if has_ledger and rescale_ledger_entries:
        factor = Decimal(conversion_factor_oldbase_to_newbase)
        entries = list(InventoryLedger.objects.filter(inventory_item=item))
        for e in entries:
            e.qty_delta = (Decimal(e.qty_delta) / factor).quantize(Decimal("0.0001"))
        InventoryLedger.objects.bulk_update(entries, ["qty_delta"])

    if item.retail and not InventoryQtyVariations.objects.filter(inventory=item, is_default_sell_uom=True, active=True).exists():
        set_default_sell_uom(item=item, uom=target)
    if item.supplies and not InventoryQtyVariations.objects.filter(inventory=item, is_default_receive_uom=True, active=True).exists():
        set_default_receive_uom(item=item, uom=target)

    return target

@transaction.atomic
def set_base_uom_by_measurement(*, item: InventoryMaster, measurement: Measurement) -> InventoryQtyVariations:
    # Find or create base row (qty=1)
    uom, _ = InventoryQtyVariations.objects.get_or_create(
        inventory=item,
        variation=measurement,
        variation_qty=Decimal("1.0000"),
        defaults={"active": True},
    )

    # Clear other base flags
    InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True).exclude(pk=uom.pk).update(is_base_unit=False)

    # Mark this as base
    changed = False
    if not uom.is_base_unit:
        uom.is_base_unit = True
        changed = True
    if not uom.active:
        uom.active = True
        changed = True
    if uom.variation_qty != Decimal("1.0000"):
        uom.variation_qty = Decimal("1.0000")
        changed = True

    if changed:
        uom.save()

    return uom


@transaction.atomic
def set_default_sell_by_measurement(
    *, item: InventoryMaster, measurement: Measurement, variation_qty: Decimal = Decimal("1.0000")
) -> InventoryQtyVariations:
    variation_qty = Decimal(variation_qty or 1)
    if variation_qty <= 0:
        raise ValidationError("Sell qty must be > 0")

    uom, _ = InventoryQtyVariations.objects.get_or_create(
        inventory=item,
        variation=measurement,
        variation_qty=variation_qty,
        defaults={"active": True},
    )

    # Clear other default sell flags
    InventoryQtyVariations.objects.filter(inventory=item, is_default_sell_uom=True).exclude(pk=uom.pk).update(
        is_default_sell_uom=False
    )

    if not uom.is_default_sell_uom or not uom.active:
        uom.is_default_sell_uom = True
        uom.active = True
        uom.save(update_fields=["is_default_sell_uom", "active"])

    return uom


@transaction.atomic
def set_default_receive_by_measurement(
    *, item: InventoryMaster, measurement: Measurement, variation_qty: Decimal = Decimal("1.0000")
) -> InventoryQtyVariations:
    variation_qty = Decimal(variation_qty or 1)
    if variation_qty <= 0:
        raise ValidationError("Receive qty must be > 0")

    uom, _ = InventoryQtyVariations.objects.get_or_create(
        inventory=item,
        variation=measurement,
        variation_qty=variation_qty,
        defaults={"active": True},
    )

    # Clear other default receive flags
    InventoryQtyVariations.objects.filter(inventory=item, is_default_receive_uom=True).exclude(pk=uom.pk).update(
        is_default_receive_uom=False
    )

    if not uom.is_default_receive_uom or not uom.active:
        uom.is_default_receive_uom = True
        uom.active = True
        uom.save(update_fields=["is_default_receive_uom", "active"])

    return uom