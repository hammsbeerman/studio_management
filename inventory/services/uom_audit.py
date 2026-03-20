from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, List, Optional, Dict
from collections import defaultdict, Counter

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q

from controls.models import Measurement  # ✅ measurement lives in controls
from inventory.models import InventoryMaster, InventoryQtyVariations, InventoryLedger

from inventory.services.uom_rows import get_or_create_uom_row
from inventory.services.uoms import ensure_base_uom, set_default_sell_uom, set_default_receive_uom

from inventory.services.item_usage import classify_item_usage, ItemUsage


# -------------------------------------------------------------------
# Canonical Measurement Alias Map
# -------------------------------------------------------------------
# Canonical: "Each" (id=16), aliases include "Ea" (id=1)
# Canonical: "Sht"  (id=4), aliases include "Sheet", "Sheets"
CANONICAL_MEASUREMENT_ALIASES: Dict[str, List[str]] = {
    "Each": ["Ea"],
    "Sht": ["Sheet", "Sheets"],
}

BASE_QTY = Decimal("1.0000")

ISSUE = {
    "NO_BASE": "No active base UOM set",
    "MULTI_BASE": "Multiple base UOM rows found",
    "BASE_QTY_NOT_ONE": "Base UOM variation_qty must be 1.0000",

    "DEFAULT_SELL_MISSING": "No active default SELL UOM set",
    "DEFAULT_RECEIVE_MISSING": "No active default RECEIVE UOM set",
    "MULTI_DEFAULT_SELL": "Multiple default SELL UOM rows found",
    "MULTI_DEFAULT_RECEIVE": "Multiple default RECEIVE UOM rows found",
    "DEFAULT_SELL_INACTIVE": "Default SELL UOM is inactive",
    "DEFAULT_RECEIVE_INACTIVE": "Default RECEIVE UOM is inactive",

    "DUPLICATE_MEASUREMENT_ROWS": "Duplicate rows for the same measurement",
    "SELL_QTY_INVALID": "Default SELL variation_qty must be > 0",
    "RECEIVE_QTY_INVALID": "Default RECEIVE variation_qty must be > 0",

    "ROUNDING_WITHOUT_FRACTIONAL": "rounding_increment set but allow_fractional_qty=False",
    "LEGACY_BASE_MISMATCH": "primary_base_unit does not match active base UOM",

    "SELL_BELOW_BASE_QTY": "Default sell qty < 1 while fractional disabled",
    "RECEIVE_SMALLER_THAN_SELL": "Receive qty is smaller than sell qty",
    "BASE_ONLY_NO_DEFAULTS": "Base exists but no sell/receive defaults configured",
    "FRACTIONAL_WITHOUT_INCREMENT": "Fractional qty allowed but no rounding increment set",

    "FLAGGED_INACTIVE": "A base/default UOM row is flagged but inactive",
    "NULL_MEASUREMENT": "A variation row has no measurement (variation_id is NULL)",

    "SAFE_TO_ARCHIVE": "Eligible for archive (no history/references).",

}

LEDGER_MODE_BLOCK = "block"
LEDGER_MODE_SAFE = "safe"

def item_has_ledger_history(item: InventoryMaster) -> bool:
    return InventoryLedger.objects.filter(inventory_item=item).exists()


# -------------------------
# Audit types
# -------------------------

@dataclass
class BulkApplyStats:
    scanned: int = 0
    selected: int = 0
    normalized: int = 0
    normalized_skipped_ledger: int = 0
    deactivated_rows: int = 0
    deactivated_skipped_used: int = 0
    deactivated_skipped_flagged: int = 0
    marked_non_inventory: int = 0
    marked_non_inventory_skipped_ledger: int = 0
    errors: int = 0

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
    usage: Optional["ItemUsage"] = None  # ← add this

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
        qs = qs.filter(name__icontains=name_contains)

    if not include_non_inventory:
        qs = qs.filter(non_inventory=False)

    # if you have flags like these, keep; otherwise harmless if always False in callers
    if retail_only:
        qs = qs.filter(retail=True)

    if supplies_only:
        qs = qs.filter(supplies=True)

    qs = qs.prefetch_related(
        Prefetch(
            "variations",
            queryset=InventoryQtyVariations.objects.select_related("variation").order_by("id"),
        )
    )
    return qs


# -------------------------
# Wrapper expected by views
# -------------------------

def audit_uoms(
    *,
    only_active: bool = True,
    vendor_id: Optional[int] = None,
    name_contains: str = "",
    retail_only: bool = False,
    supplies_only: bool = False,
    include_non_inventory: bool = False,
    limit: int = 200,
) -> UomAuditResult:
    """
    Convenience wrapper used by the admin view.

    Builds the queryset via build_items_for_uom_audit(), applies a limit, then runs audit_uom_for_items().
    """
    qs = build_items_for_uom_audit(
        only_active=only_active,
        vendor_id=vendor_id,
        name_contains=name_contains,
        retail_only=retail_only,
        supplies_only=supplies_only,
        include_non_inventory=include_non_inventory,
    )

    if limit:
        qs = qs[: int(limit)]

    return audit_uom_for_items(qs)


# -------------------------
# Audit logic
# -------------------------

def audit_uom_for_items(items: Iterable["InventoryMaster"]) -> "UomAuditResult":
    rows: List[UomAuditRow] = []
    summary = UomAuditSummary()

    # ---- Pre-load canonical + alias Measurements for alias-mix detection ----
    canonical_names = list(CANONICAL_MEASUREMENT_ALIASES.keys())
    all_alias_names = [a for aliases in CANONICAL_MEASUREMENT_ALIASES.values() for a in aliases]

    name_to_measurement = {
        m.name: m
        for m in Measurement.objects.filter(Q(name__in=canonical_names) | Q(name__in=all_alias_names))
    }

    def add_issue(row: UomAuditRow, code: str, message: Optional[str] = None) -> None:
        row.issues.append(UomIssue(code=code, message=message or ISSUE.get(code, code)))

    def has_issue(row: UomAuditRow, code: str) -> bool:
        return any(i.code == code for i in row.issues)

    def qty_or_zero(v: "InventoryQtyVariations") -> Decimal:
        return v.variation_qty if v.variation_qty is not None else Decimal("0")

    for item in items:
        variations = list(getattr(item, "variations", []).all()) if hasattr(item, "variations") else []
        active = [v for v in variations if v.active]

        def first_active(flag: str) -> Optional["InventoryQtyVariations"]:
            return next((v for v in active if getattr(v, flag, False)), None)

        # Display choices (prefer active)
        base = first_active("is_base_unit")
        default_sell = first_active("is_default_sell_uom")
        default_receive = first_active("is_default_receive_uom")

        row = UomAuditRow(
            item=item,
            base=base,
            default_sell=default_sell,
            default_receive=default_receive,
            issues=[],
        )

        # ---- Usage intelligence (archive candidates, etc.) ----
        from inventory.services.item_usage import classify_item_usage

        usage = classify_item_usage(item)
        row.usage = usage
        if usage.safe_to_archive:
            add_issue(row, "SAFE_TO_ARCHIVE", "No history or references. Eligible for archive.")

        # ---- Duplicate exact rows: same measurement + same qty (active or inactive) ----
        by_key = defaultdict(int)
        for v in variations:
            if not v.variation_id:
                continue
            by_key[(v.variation_id, qty_or_zero(v))] += 1

        if any(cnt > 1 for cnt in by_key.values()):
            add_issue(row, "DUPLICATE_MEASUREMENT_ROWS", "Duplicate rows exist for the same measurement and qty.")

        # ---- Base checks ----
        base_all = [v for v in variations if v.is_base_unit]
        base_active = [v for v in active if v.is_base_unit]

        if len(base_all) > 1:
            add_issue(row, "MULTI_BASE")

        base_for_legacy: Optional["InventoryQtyVariations"] = None
        if not base_active:
            add_issue(row, "NO_BASE")
        else:
            base_for_legacy = base_active[0]
            if (base_for_legacy.variation_qty or Decimal("0")) != BASE_QTY:
                add_issue(row, "BASE_QTY_NOT_ONE")

        # ---- Default sell checks ----
        sell_all = [v for v in variations if v.is_default_sell_uom]
        sell_active = [v for v in active if v.is_default_sell_uom]

        if len(sell_all) > 1:
            add_issue(row, "MULTI_DEFAULT_SELL")

        if not sell_active:
            if sell_all:
                add_issue(row, "DEFAULT_SELL_INACTIVE")
            add_issue(row, "DEFAULT_SELL_MISSING")
        else:
            s = sell_active[0]
            if s.variation_qty is None or s.variation_qty <= 0:
                add_issue(row, "SELL_QTY_INVALID")

        # ---- Default receive checks ----
        recv_all = [v for v in variations if v.is_default_receive_uom]
        recv_active = [v for v in active if v.is_default_receive_uom]

        if len(recv_all) > 1:
            add_issue(row, "MULTI_DEFAULT_RECEIVE")

        if not recv_active:
            if recv_all:
                add_issue(row, "DEFAULT_RECEIVE_INACTIVE")
            add_issue(row, "DEFAULT_RECEIVE_MISSING")
        else:
            r = recv_active[0]
            if r.variation_qty is None or r.variation_qty <= 0:
                add_issue(row, "RECEIVE_QTY_INVALID")

        # ---- Rounding consistency ----
        if any(v.rounding_increment is not None and not v.allow_fractional_qty for v in variations):
            add_issue(row, "ROUNDING_WITHOUT_FRACTIONAL")

        if any(v.allow_fractional_qty and not v.rounding_increment for v in variations):
            add_issue(row, "FRACTIONAL_WITHOUT_INCREMENT")

        # ---- Legacy mismatch ----
        if item.primary_base_unit_id and base_for_legacy and base_for_legacy.variation_id != item.primary_base_unit_id:
            add_issue(row, "LEGACY_BASE_MISMATCH")

        # ---- Alias mix detection ----
        used_ids = {v.variation_id for v in variations if v.variation_id}
        for canonical, aliases in CANONICAL_MEASUREMENT_ALIASES.items():
            canon_m = name_to_measurement.get(canonical)
            if not canon_m:
                continue

            alias_ms = [name_to_measurement.get(a) for a in aliases]
            alias_ms = [am for am in alias_ms if am]
            if not alias_ms:
                continue

            canon_used = canon_m.id in used_ids
            alias_used = any(am.id in used_ids for am in alias_ms)

            if canon_used and alias_used:
                add_issue(
                    row,
                    "ALIAS_MIX",
                    f"Mix of canonical '{canonical}' and alias measurements ({', '.join(aliases)}).",
                )

        # ---- Flagged-but-inactive rows (should not happen) ----
        # If any inactive row is flagged base/default, we should flag it.
        # Avoid firing this if there are simply NO active bases (NO_BASE already covers that scenario).
        flagged_inactive = any(
            (v.is_base_unit or v.is_default_sell_uom or v.is_default_receive_uom) and not v.active
            for v in variations
        )
        if flagged_inactive and not has_issue(row, "NO_BASE"):
            add_issue(row, "FLAGGED_INACTIVE")

        # ---- Rows missing measurement FK ----
        if any(v.variation_id is None for v in variations):
            add_issue(row, "NULL_MEASUREMENT")

        # ---- Policy checks ----
        if sell_active:
            s = sell_active[0]
            if s.variation_qty is not None and s.variation_qty < Decimal("1") and not s.allow_fractional_qty:
                add_issue(row, "SELL_BELOW_BASE_QTY")

        if sell_active and recv_active:
            s = sell_active[0]
            r = recv_active[0]
            if s.variation_qty and r.variation_qty and r.variation_qty < s.variation_qty:
                add_issue(row, "RECEIVE_SMALLER_THAN_SELL")

        if base_active and not sell_active and not recv_active:
            add_issue(row, "BASE_ONLY_NO_DEFAULTS")

        # ---- Summary ----
        summary.matched += 1
        if row.ok:
            summary.ok += 1
        else:
            summary.with_issues += 1
            for issue in row.issues:
                summary.by_issue_code[issue.code] = summary.by_issue_code.get(issue.code, 0) + 1

        rows.append(row)

    return UomAuditResult(rows=rows, summary=summary)



# -------------------------
# Fix helpers (already used)
# -------------------------

@transaction.atomic
def deactivate_uom_rows(*, item: InventoryMaster, uom_ids: list[int]) -> dict:
    if not uom_ids:
        return {
            "requested": 0, "deactivated": 0,
            "skipped_flagged": 0, "skipped_used": 0, "skipped_missing": 0,
            "deactivated_labels": [], "skipped_used_labels": [], "skipped_flagged_labels": [],
        }

    qs = InventoryQtyVariations.objects.filter(inventory=item, id__in=uom_ids).select_related("variation")

    found_ids = set(qs.values_list("id", flat=True))
    skipped_missing = len(set(uom_ids) - found_ids)

    used_ids = bulk_uom_used_ids(list(found_ids))

    skipped_flagged = 0
    skipped_used = 0
    deactivated = 0

    deactivated_labels: list[str] = []
    skipped_used_labels: list[str] = []
    skipped_flagged_labels: list[str] = []

    for u in qs.select_for_update():
        label = f"{u.variation.name}×{u.variation_qty}"

        if u.is_base_unit or u.is_default_sell_uom or u.is_default_receive_uom:
            skipped_flagged += 1
            skipped_flagged_labels.append(label)
            continue

        if u.id in used_ids:
            skipped_used += 1
            skipped_used_labels.append(label)
            continue

        if u.active:
            u.active = False
            u.save(update_fields=["active"])
            deactivated += 1
            deactivated_labels.append(label)

    return {
        "requested": len(uom_ids),
        "deactivated": deactivated,
        "skipped_flagged": skipped_flagged,
        "skipped_used": skipped_used,
        "skipped_missing": skipped_missing,
        "deactivated_labels": deactivated_labels,
        "skipped_used_labels": skipped_used_labels,
        "skipped_flagged_labels": skipped_flagged_labels,
    }

def _get_model_or_none(app_label: str, model_name: str):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None


def uom_used_in_history(uom_id: int) -> bool:
    """
    True if InventoryQtyVariations row is referenced by any historical line items.
    """
    InvoiceItem = _get_model_or_none("finance", "InvoiceItem")
    RetailSaleLine = _get_model_or_none("retail", "RetailSaleLine")

    used = False
    if InvoiceItem:
        used = used or InvoiceItem.objects.filter(invoice_unit_id=uom_id).exists()
    if RetailSaleLine:
        used = used or RetailSaleLine.objects.filter(sold_variation_id=uom_id).exists()
    return used


def bulk_uom_used_ids(uom_ids: Iterable[int]) -> set[int]:
    """Return UOM variation IDs that are referenced by history tables.

    In this repo, InventoryQtyVariations is referenced by:
      - finance.InvoiceItem.invoice_unit (CASCADE)
      - retail.RetailSaleLine.sold_variation (SET_NULL)
    """
    uom_ids = [int(x) for x in uom_ids if x]
    if not uom_ids:
        return set()

    used: set[int] = set()

    from finance.models import InvoiceItem
    from retail.models import RetailSaleLine

    used.update(
        InvoiceItem.objects.filter(invoice_unit_id__in=uom_ids)
        .values_list("invoice_unit_id", flat=True)
        .distinct()
    )
    used.update(
        RetailSaleLine.objects.filter(sold_variation_id__in=uom_ids)
        .values_list("sold_variation_id", flat=True)
        .distinct()
    )

    return {int(x) for x in used if x is not None}



@transaction.atomic
def set_base_uom(*, item: InventoryMaster, uom: InventoryQtyVariations) -> InventoryQtyVariations:
    """
    Guarded base setter: blocks if known ledger history exists.
    """
    if InventoryLedger.objects.filter(inventory_item=item).exists():
        raise ValidationError("Item has ledger history; base UOM change is blocked.")

    return ensure_base_uom(item=item, measurement=uom.variation, activate=True)


@transaction.atomic
def set_base_uom_by_measurement(*, item: InventoryMaster, measurement: Measurement) -> InventoryQtyVariations:
    """
    Convenience for the UI: ensure base row exists for measurement and set base flags.
    """
    return ensure_base_uom(item=item, measurement=measurement, activate=True)


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

# ------------------------------------------------------------
# Normalization helpers (kept for future use / alias tools)
# ------------------------------------------------------------

def _measurement_alias_map() -> Dict[int, int]:
    """
    Returns {alias_measurement_id: canonical_measurement_id} for the configured alias set.
    """
    if not CANONICAL_MEASUREMENT_ALIASES:
        return {}

    # Fetch all measurement ids involved
    names: List[str] = []
    for canon, aliases in CANONICAL_MEASUREMENT_ALIASES.items():
        names.append(canon)
        names.extend(aliases)

    ms = list(Measurement.objects.filter(name__in=names))
    by_name = {m.name: m for m in ms}

    out: Dict[int, int] = {}
    for canon_name, alias_names in CANONICAL_MEASUREMENT_ALIASES.items():
        canon = by_name.get(canon_name)
        if not canon:
            continue
        for alias_name in alias_names:
            alias = by_name.get(alias_name)
            if alias:
                out[alias.id] = canon.id

    return out


def normalize_variation_measurements(
    *,
    item: InventoryMaster,
    dry_run: bool = True,
) -> Dict[str, int]:
    """
    Normalize variation.measurement FK values for an item using CANONICAL_MEASUREMENT_ALIASES.

    NOTE: This does not change base/default flags. It only changes FK references for aliases -> canonical.
    """
    alias_to_canon = _measurement_alias_map()
    if not alias_to_canon:
        return {"scanned": 0, "changed": 0}

    qs = InventoryQtyVariations.objects.filter(inventory=item).select_related("variation")
    scanned = 0
    changed = 0

    for row in qs:
        scanned += 1
        if not row.variation_id:
            continue
        new_id = alias_to_canon.get(row.variation_id)
        if not new_id or new_id == row.variation_id:
            continue

        changed += 1
        if not dry_run:
            row.variation_id = new_id
            row.save(update_fields=["variation"])

    return {"scanned": scanned, "changed": changed}


def normalize_measurements_for_queryset(
    *,
    items: Iterable[InventoryMaster],
    dry_run: bool = True,
) -> Dict[str, int]:
    """
    Normalize measurement aliases for a list/queryset of items.
    """
    scanned_items = 0
    total_scanned = 0
    total_changed = 0

    for item in items:
        scanned_items += 1
        res = normalize_variation_measurements(item=item, dry_run=dry_run)
        total_scanned += res.get("scanned", 0)
        total_changed += res.get("changed", 0)

    return {
        "items": scanned_items,
        "scanned_rows": total_scanned,
        "changed_rows": total_changed,
    }

def has_ledger(item_id: int) -> bool:
    return InventoryLedger.objects.filter(inventory_item_id=item_id).exists()


def _pick_best_uom(
    rows: list[InventoryQtyVariations],
    *,
    prefer_pk: Optional[int] = None,
) -> Optional[InventoryQtyVariations]:
    """
    Duplicate-resolution picker.

    Preference (highest wins):
      1) prefer_pk (default sell/receive/base row you want to keep)
      2) flagged base/default (any of the 3 flags)
      3) qty == 1.0000
      4) qty closest to 1.0000
      5) active
      6) lowest id
    """
    if not rows:
        return None

    if prefer_pk is not None:
        for r in rows:
            if r.pk == prefer_pk:
                return r

    def qty_of(v: InventoryQtyVariations) -> Decimal:
        try:
            return v.variation_qty if v.variation_qty is not None else Decimal("0")
        except Exception:
            return Decimal("0")

    def key(v: InventoryQtyVariations):
        q = qty_of(v)
        flagged = 1 if (v.is_base_unit or v.is_default_sell_uom or v.is_default_receive_uom) else 0
        exact_one = 1 if q == BASE_QTY else 0
        # smaller distance is better → use negative distance so "bigger is better"
        distance = abs(q - BASE_QTY)
        active = 1 if v.active else 0
        # lower id is better → use negative id so "bigger is better"
        vid = v.id or 0
        return (flagged, exact_one, -distance, active, -vid)

    # max() avoids reverse/neg confusion and works fine with Decimals in tuples
    return max(rows, key=key)

@transaction.atomic
def normalize_item_uoms(
    *,
    item: InventoryMaster,
    dry_run: bool = False,
    ledger_mode: str = LEDGER_MODE_BLOCK,
) -> dict:
    actions: list[str] = []
    stats = {
        "dry_run": int(bool(dry_run)),
        "ledger": 0,
        "ledger_mode": ledger_mode,
        "dupe_groups": 0,
        "dupe_rows_inactivated": 0,
        "flags_cleared": 0,
        "qty_fixed": 0,
        "base_set": 0,
        "sell_set": 0,
        "recv_set": 0,
    }

    # normalize ledger_mode
    ledger_mode_norm = (ledger_mode or "").strip().upper()
    if ledger_mode_norm in ("SAFE", "LEDGER_SAFE"):
        ledger_mode_norm = LEDGER_MODE_SAFE
    else:
        ledger_mode_norm = LEDGER_MODE_BLOCK
    stats["ledger_mode"] = ledger_mode_norm

    ledger_exists = has_ledger(item.id)
    stats["ledger"] = int(ledger_exists)

    if ledger_exists and ledger_mode_norm == LEDGER_MODE_BLOCK:
        raise ValidationError("Item has ledger history; normalize is blocked.")

    def save(uom: InventoryQtyVariations, *, update_fields: list[str], note: str) -> None:
        actions.append(note)
        if not dry_run:
            uom.save(update_fields=update_fields)

    def bulk_update(qs, *, fields: dict, note: str) -> int:
        actions.append(note)
        if dry_run:
            return 0
        return qs.update(**fields)

    def pick_keep(flagged: list[InventoryQtyVariations]) -> InventoryQtyVariations:
        # prefer active, then lowest id
        return sorted(flagged, key=lambda v: (0 if v.active else 1, v.id or 0))[0]

    # Load rows
    variations = list(
        InventoryQtyVariations.objects
        .filter(inventory=item)
        .select_related("variation")
        .order_by("id")
    )
    active = [v for v in variations if v.active]

    # -------------------------
    # LEDGER SAFE MODE
    # -------------------------
    if ledger_exists and ledger_mode_norm == LEDGER_MODE_SAFE:
        # only clear MULTI flags; no qty/active/create/deactivate
        def keep_one(flag: str) -> None:
            flagged = [v for v in variations if getattr(v, flag)]
            if len(flagged) <= 1:
                return
            keep = pick_keep(flagged)
            for o in flagged:
                if o.pk == keep.pk:
                    continue
                setattr(o, flag, False)
                save(o, update_fields=[flag], note=f"[ledger-safe] clear {flag} on row {o.id}")
                stats["flags_cleared"] += 1

        keep_one("is_base_unit")
        keep_one("is_default_sell_uom")
        keep_one("is_default_receive_uom")

        return {"stats": stats, "actions": actions}

    # -------------------------
    # FULL NORMALIZE (NO LEDGER)
    # -------------------------

    # ---- 1) De-dup exact duplicates: same (measurement_id, qty) ----
    by_key: dict[tuple[int, Decimal], list[InventoryQtyVariations]] = defaultdict(list)
    for v in variations:
        if not v.variation_id:
            continue
        qty = v.variation_qty if v.variation_qty is not None else Decimal("0")
        by_key[(v.variation_id, qty)].append(v)

    for (mid, qty), rows in by_key.items():
        if len(rows) <= 1:
            continue

        stats["dupe_groups"] += 1

        # prefer a flagged row if present; else prefer active; else lowest id
        prefer_pk = None
        for r in rows:
            if r.is_base_unit or r.is_default_sell_uom or r.is_default_receive_uom:
                prefer_pk = r.pk
                break

        keep = _pick_best_uom(rows, prefer_pk=prefer_pk)
        if not keep:
            continue

        keep_changed = False
        for other in rows:
            if other.pk == keep.pk:
                continue

            # merge flags onto keep
            if other.is_base_unit and not keep.is_base_unit:
                keep.is_base_unit = True
                keep_changed = True
            if other.is_default_sell_uom and not keep.is_default_sell_uom:
                keep.is_default_sell_uom = True
                keep_changed = True
            if other.is_default_receive_uom and not keep.is_default_receive_uom:
                keep.is_default_receive_uom = True
                keep_changed = True

            # clear flags + inactivate dup
            if other.is_base_unit or other.is_default_sell_uom or other.is_default_receive_uom:
                stats["flags_cleared"] += 1

            other.is_base_unit = False
            other.is_default_sell_uom = False
            other.is_default_receive_uom = False

            if other.active:
                other.active = False
                stats["dupe_rows_inactivated"] += 1

            save(
                other,
                update_fields=["is_base_unit", "is_default_sell_uom", "is_default_receive_uom", "active"],
                note=f"dedupe: inactivate exact-duplicate row {other.id} (measurement_id={mid}, qty={qty})",
            )

        if keep_changed:
            save(
                keep,
                update_fields=["is_base_unit", "is_default_sell_uom", "is_default_receive_uom"],
                note=f"dedupe: merged flags onto kept row {keep.id} (measurement_id={mid}, qty={qty})",
            )

    # Refresh after dedupe
    variations = list(
        InventoryQtyVariations.objects
        .filter(inventory=item)
        .select_related("variation")
        .order_by("id")
    )
    active = [v for v in variations if v.active]

    # ---- 2) Ensure ONE base ----
    base_active = [v for v in active if v.is_base_unit]
    base_all = [v for v in variations if v.is_base_unit]
    base = base_active[0] if base_active else (base_all[0] if base_all else None)

    if base:
        cleared = bulk_update(
            InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True).exclude(pk=base.pk),
            fields={"is_base_unit": False},
            note=f"base: clear extra base flags (keep row {base.id})",
        )
        stats["flags_cleared"] += int(cleared or 0)

        changed = False
        if not base.active:
            base.active = True
            changed = True
        if (base.variation_qty or Decimal("0")) != BASE_QTY:
            base.variation_qty = BASE_QTY
            changed = True
            stats["qty_fixed"] += 1
        if not base.is_base_unit:
            base.is_base_unit = True
            changed = True

        if changed:
            save(base, update_fields=["active", "variation_qty", "is_base_unit"], note=f"base: normalize row {base.id}")
            stats["base_set"] += 1

    # ---- 3) Ensure ONE default sell ----
    sell_active = [v for v in active if v.is_default_sell_uom]
    sell_all = [v for v in variations if v.is_default_sell_uom]
    sell = sell_active[0] if sell_active else (sell_all[0] if sell_all else None)

    if not sell and base:
        sell = base
        sell.is_default_sell_uom = True
        sell.active = True
        save(sell, update_fields=["is_default_sell_uom", "active"], note=f"sell: set missing default sell -> base row {sell.id}")
        stats["sell_set"] += 1

    if sell:
        cleared = bulk_update(
            InventoryQtyVariations.objects.filter(inventory=item, is_default_sell_uom=True).exclude(pk=sell.pk),
            fields={"is_default_sell_uom": False},
            note=f"sell: clear extra default sell flags (keep row {sell.id})",
        )
        stats["flags_cleared"] += int(cleared or 0)

        changed = False
        if not sell.active:
            sell.active = True
            changed = True
        if not sell.is_default_sell_uom:
            sell.is_default_sell_uom = True
            changed = True
        if sell.variation_qty is None or sell.variation_qty <= 0:
            sell.variation_qty = Decimal("1.0000")
            changed = True
            stats["qty_fixed"] += 1

        if changed:
            save(sell, update_fields=["active", "is_default_sell_uom", "variation_qty"], note=f"sell: normalize row {sell.id}")
            stats["sell_set"] += 1

    # ---- 4) Ensure ONE default receive ----
    recv_active = [v for v in active if v.is_default_receive_uom]
    recv_all = [v for v in variations if v.is_default_receive_uom]
    recv = recv_active[0] if recv_active else (recv_all[0] if recv_all else None)

    if not recv and base:
        recv = base
        recv.is_default_receive_uom = True
        recv.active = True
        save(recv, update_fields=["is_default_receive_uom", "active"], note=f"recv: set missing default receive -> base row {recv.id}")
        stats["recv_set"] += 1

    if recv:
        cleared = bulk_update(
            InventoryQtyVariations.objects.filter(inventory=item, is_default_receive_uom=True).exclude(pk=recv.pk),
            fields={"is_default_receive_uom": False},
            note=f"recv: clear extra default receive flags (keep row {recv.id})",
        )
        stats["flags_cleared"] += int(cleared or 0)

        changed = False
        if not recv.active:
            recv.active = True
            changed = True
        if not recv.is_default_receive_uom:
            recv.is_default_receive_uom = True
            changed = True
        if recv.variation_qty is None or recv.variation_qty <= 0:
            recv.variation_qty = Decimal("1.0000")
            changed = True
            stats["qty_fixed"] += 1

        if changed:
            save(recv, update_fields=["active", "is_default_receive_uom", "variation_qty"], note=f"recv: normalize row {recv.id}")
            stats["recv_set"] += 1

    return {"stats": stats, "actions": actions}


def bulk_deactivate_unused_variations_for_item(
    *,
    item: InventoryMaster,
    dry_run: bool = False,
) -> dict:
    """
    Deactivate ALL active rows that are:
      - not base, not default sell, not default receive
      - not used in history
    """
    qs = InventoryQtyVariations.objects.filter(inventory=item, active=True)
    candidate_ids = []
    for v in qs:
        if v.is_base_unit or v.is_default_sell_uom or v.is_default_receive_uom:
            continue
        candidate_ids.append(v.id)

    if dry_run:
        used_ids = bulk_uom_used_ids(candidate_ids)
        rows = InventoryQtyVariations.objects.filter(
            inventory=item,
            id__in=candidate_ids,
        ).select_related("variation")

        deactivated = 0
        skipped_flagged = 0
        skipped_used = 0
        labels = []

        for u in rows:
            label = f"{u.variation.name}×{u.variation_qty}"
            if u.is_base_unit or u.is_default_sell_uom or u.is_default_receive_uom:
                skipped_flagged += 1
                continue
            if u.id in used_ids:
                skipped_used += 1
                continue
            if u.active:
                deactivated += 1
                labels.append(label)

        return {
            "requested": len(candidate_ids),
            "deactivated": deactivated,
            "skipped_flagged": skipped_flagged,
            "skipped_used": skipped_used,
            "skipped_missing": 0,
            "deactivated_labels": labels,
            "skipped_used_labels": [],
            "skipped_flagged_labels": [],
        }

    return deactivate_uom_rows(item=item, uom_ids=candidate_ids)



def bulk_apply_to_queryset(
    *,
    only_active: bool = True,
    vendor_id: Optional[int] = None,
    name_contains: str = "",
    include_non_inventory: bool = False,
    limit: int = 200,
    selected_item_ids: Optional[list[int]] = None,
    action: str,
    normalize_mode: str = "safe",  # "safe" or "ledger_safe"
    dry_run: bool = False,
    selected_measurement_ids: Optional[list[int]] = None,
) -> BulkApplyStats:
    stats = BulkApplyStats()

    qs = build_items_for_uom_audit(
        only_active=only_active,
        vendor_id=vendor_id,
        name_contains=name_contains,
        retail_only=False,
        supplies_only=False,
        include_non_inventory=include_non_inventory,
    )

    # selection: None => whole filtered set, [] => none (treat as whole set in your UI),
    # list => selected only
    if selected_item_ids:
        qs = qs.filter(id__in=selected_item_ids)

    if limit:
        qs = qs[: int(limit)]

    # ---- One-query ledger map for the scanned set ----
    item_ids = list(qs.values_list("id", flat=True))
    ledger_item_ids = set(
        InventoryLedger.objects.filter(inventory_item_id__in=item_ids)
        .values_list("inventory_item_id", flat=True)
        .distinct()
    )

    # for selection accounting
    selected_mode = selected_item_ids is not None

    for item in qs:
        stats.scanned += 1
        if selected_mode:
            stats.selected += 1

        try:
            item_has_ledger = item.id in ledger_item_ids

            if action == "normalize":
                if normalize_mode == "ledger_safe":
                    # allowed even with ledger, but should be "ledger-safe" behavior in normalize_item_uoms
                    normalize_item_uoms(
                        item=item,
                        dry_run=dry_run,
                        ledger_mode="SAFE",   # ledger-safe mode
                    )
                    stats.normalized += 1
                else:
                    # safe mode: SKIP ledger items entirely
                    if item_has_ledger:
                        stats.normalized_skipped_ledger += 1
                        continue

                    normalize_item_uoms(
                        item=item,
                        dry_run=dry_run,
                        ledger_mode="BLOCK",  # but we're only here when NO ledger exists
                    )
                    stats.normalized += 1

            elif action == "deactivate_unused":
                res = bulk_deactivate_unused_variations_for_item(item=item, dry_run=dry_run)
                stats.deactivated_rows += res.get("deactivated", 0)
                stats.deactivated_skipped_used += res.get("skipped_used", 0)
                stats.deactivated_skipped_flagged += res.get("skipped_flagged", 0)

            elif action == "deactivate_by_measurement":
                measurement_ids = selected_measurement_ids or []
                res = bulk_deactivate_by_measurements_for_item(
                    item=item,
                    measurement_ids=measurement_ids,
                    dry_run=dry_run,
                )
                stats.deactivated_rows += res.get("deactivated", 0)
                stats.deactivated_skipped_used += res.get("skipped_used", 0)
                stats.deactivated_skipped_flagged += res.get("skipped_flagged", 0)

            elif action == "deactivate_duplicates":
                res = bulk_deactivate_duplicates_keep_one_for_item(item=item, dry_run=dry_run)
                stats.deactivated_rows += res.get("deactivated", 0)
                stats.deactivated_skipped_used += res.get("skipped_used", 0)
                stats.deactivated_skipped_flagged += res.get("skipped_flagged", 0)

            elif action == "mark_non_inventory":
                if item_has_ledger:
                    stats.marked_non_inventory_skipped_ledger += 1
                    continue
                if item.non_inventory:
                    continue
                if not dry_run:
                    item.non_inventory = True
                    item.save(update_fields=["non_inventory"])
                stats.marked_non_inventory += 1

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception:
            stats.errors += 1

    return stats

def bulk_deactivate_by_measurements_for_item(
    *,
    item: InventoryMaster,
    measurement_ids: list[int],
    dry_run: bool = False,
) -> dict:
    """
    Deactivate ALL active rows for an item whose variation_id is in measurement_ids,
    with guardrails enforced by deactivate_uom_rows():
      - not base/default sell/default receive
      - not used in history
      - no deletes, only active=False
    """
    if not measurement_ids:
        return {
            "requested": 0,
            "deactivated": 0,
            "skipped_flagged": 0,
            "skipped_used": 0,
            "skipped_missing": 0,
        }

    qs = InventoryQtyVariations.objects.filter(
        inventory=item,
        active=True,
        variation_id__in=measurement_ids,
    ).select_related("variation")
    uom_ids = list(qs.values_list("id", flat=True))

    if dry_run:
        used_ids = bulk_uom_used_ids(uom_ids)

        deactivated = 0
        skipped_flagged = 0
        skipped_used = 0

        for u in qs:
            if u.is_base_unit or u.is_default_sell_uom or u.is_default_receive_uom:
                skipped_flagged += 1
                continue
            if u.id in used_ids:
                skipped_used += 1
                continue
            deactivated += 1

        return {
            "requested": len(uom_ids),
            "deactivated": deactivated,
            "skipped_flagged": skipped_flagged,
            "skipped_used": skipped_used,
            "skipped_missing": 0,
        }

    return deactivate_uom_rows(item=item, uom_ids=uom_ids)


def bulk_deactivate_duplicates_keep_one_for_item(
    *,
    item: InventoryMaster,
    dry_run: bool = False,
) -> dict:
    """
    If an item has multiple rows for the same measurement_id (duplicate measurement rows),
    keep ONE row active and deactivate the others, only when safe.

    Rules:
      - Never deactivate base/default sell/default receive rows
      - Never deactivate rows used in history
      - Prefer to keep:
          1) any active row (first)
          2) otherwise any row (first)
    """
    vars_all = list(
        InventoryQtyVariations.objects.filter(inventory=item).select_related("variation")
    )
    if not vars_all:
        return {"dupe_groups": 0, "deactivated": 0, "skipped_used": 0, "skipped_flagged": 0}

    by_mid: dict[int, list[InventoryQtyVariations]] = {}
    for v in vars_all:
        if not v.variation_id:
            continue
        by_mid.setdefault(v.variation_id, []).append(v)

    dupe_groups = 0
    deactivated = 0
    skipped_used = 0
    skipped_flagged = 0

    all_ids = [v.id for v in vars_all]
    used_ids = bulk_uom_used_ids(all_ids)

    for mid, rows in by_mid.items():
        if len(rows) <= 1:
            continue
        dupe_groups += 1

        keeper = next((r for r in rows if r.active), rows[0])

        for r in rows:
            if r.id == keeper.id:
                continue

            if r.is_base_unit or r.is_default_sell_uom or r.is_default_receive_uom:
                skipped_flagged += 1
                continue
            if r.id in used_ids:
                skipped_used += 1
                continue
            if r.active:
                deactivated += 1
                if not dry_run:
                    r.active = False
                    r.save(update_fields=["active"])

    return {
        "dupe_groups": dupe_groups,
        "deactivated": deactivated,
        "skipped_used": skipped_used,
        "skipped_flagged": skipped_flagged,
    }

# def audit_item_uoms(item: InventoryMaster) -> list[str]:
#     """
#     Returns a list of issue strings for this item.
#     Assumes item.variations is prefetched.
#     """
#     issues: list[str] = []

#     vars_all = list(item.variations.all())
#     vars_active = [v for v in vars_all if v.active]

#     # Group by measurement (variation_id)
#     by_measurement = defaultdict(list)
#     for v in vars_all:
#         by_measurement[v.variation_id].append(v)

#     # Duplicate measurement rows
#     dup_meas = [mid for mid, rows in by_measurement.items() if len(rows) > 1]
#     if dup_meas:
#         issues.append(ISSUE["DUPLICATE_MEASUREMENT_ROWS"])

#     # Base checks
#     base_all = [v for v in vars_all if v.is_base_unit]
#     base_active = [v for v in vars_active if v.is_base_unit]

#     if len(base_all) > 1:
#         issues.append(ISSUE["MULTI_BASE"])

#     if not base_active:
#         issues.append(ISSUE["NO_BASE"])
#         base = None
#     else:
#         base = base_active[0]
#         if base.variation_qty != BASE_QTY:
#             issues.append(ISSUE["BASE_QTY_NOT_ONE"])

#     # Default sell checks
#     sell_all = [v for v in vars_all if v.is_default_sell_uom]
#     sell_active = [v for v in vars_active if v.is_default_sell_uom]

#     if len(sell_all) > 1:
#         issues.append(ISSUE["MULTI_DEFAULT_SELL"])

#     if not sell_active:
#         if sell_all:
#             issues.append(ISSUE["DEFAULT_SELL_INACTIVE"])
#         issues.append(ISSUE["DEFAULT_SELL_MISSING"])
#         sell = None
#     else:
#         sell = sell_active[0]
#         if sell.variation_qty is None or sell.variation_qty <= 0:
#             issues.append(ISSUE["SELL_QTY_INVALID"])

#     # Default receive checks
#     recv_all = [v for v in vars_all if v.is_default_receive_uom]
#     recv_active = [v for v in vars_active if v.is_default_receive_uom]

#     if len(recv_all) > 1:
#         issues.append(ISSUE["MULTI_DEFAULT_RECEIVE"])

#     if not recv_active:
#         if recv_all:
#             issues.append(ISSUE["DEFAULT_RECEIVE_INACTIVE"])
#         issues.append(ISSUE["DEFAULT_RECEIVE_MISSING"])
#         recv = None
#     else:
#         recv = recv_active[0]
#         if recv.variation_qty is None or recv.variation_qty <= 0:
#             issues.append(ISSUE["RECEIVE_QTY_INVALID"])

#     # Rounding / fractional consistency
#     for v in vars_all:
#         if v.rounding_increment is not None and not v.allow_fractional_qty:
#             issues.append(ISSUE["ROUNDING_WITHOUT_FRACTIONAL"])
#             break  # only need it once

#     # Legacy mismatch (if you still have primary_base_unit populated)
#     if item.primary_base_unit_id and base and base.variation_id != item.primary_base_unit_id:
#         issues.append(ISSUE["LEGACY_BASE_MISMATCH"])

#     return issues