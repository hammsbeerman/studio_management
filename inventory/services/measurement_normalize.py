from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Iterable

from django.db import transaction
from django.db.models import Q

from inventory.models import InventoryMaster, InventoryQtyVariations
from controls.models import Measurement


# Canonical targets (by name)
CANONICAL_MAP: Dict[str, List[str]] = {
    "Each": ["Ea"],
    "Sht": ["Sheet", "Sheets"],
}


@dataclass
class NormalizeRow:
    canonical_name: str
    alias_names: List[str] = field(default_factory=list)
    canonical_id: Optional[int] = None
    alias_ids: List[int] = field(default_factory=list)

    matched_variations: int = 0
    changed_variations: int = 0

    matched_primary_base_units: int = 0
    changed_primary_base_units: int = 0

    notes: List[str] = field(default_factory=list)


@dataclass
class NormalizeResult:
    dry_run: bool
    matched_items: int = 0
    rows: List[NormalizeRow] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # ✅ new counters
    missing_base_items: int = 0
    base_set_items: int = 0
    missing_default_sell_items: int = 0
    default_sell_set_items: int = 0
    missing_default_receive_items: int = 0
    default_receive_set_items: int = 0


def build_item_queryset(
    *,
    only_active: bool = True,
    vendor_id: Optional[int] = None,
    name_contains: str = "",
) -> "Iterable[InventoryMaster]":
    qs = InventoryMaster.objects.all()
    if only_active:
        qs = qs.filter(active=True)
    if vendor_id:
        qs = qs.filter(primary_vendor_id=vendor_id)
    if name_contains:
        qs = qs.filter(Q(name__icontains=name_contains) | Q(description__icontains=name_contains))
    return qs


def _get_measurement_by_name(name: str) -> Optional[Measurement]:
    return Measurement.objects.filter(name__iexact=name.strip()).first()


def _is_measurement_name(v: InventoryQtyVariations, name: str) -> bool:
    return ((getattr(v.variation, "name", "") or "").strip().lower() == name.strip().lower())


def _pick_base_candidate(item: InventoryMaster, variations: List[InventoryQtyVariations]) -> Optional[InventoryQtyVariations]:
    """
    Priority:
      1) Each × 1
      2) Sht × 1
      3) Any active × 1
      4) None
    """
    one = Decimal("1.0000")

    for v in variations:
        if v.active and Decimal(v.variation_qty or 0) == one and _is_measurement_name(v, "Each"):
            return v

    for v in variations:
        if v.active and Decimal(v.variation_qty or 0) == one and _is_measurement_name(v, "Sht"):
            return v

    for v in variations:
        if v.active and Decimal(v.variation_qty or 0) == one:
            return v

    return None


@transaction.atomic
def normalize_measurements_for_items(
    *,
    item_qs,
    do_each: bool = True,
    do_sht: bool = True,
    include_primary_base_unit: bool = True,
    fix_missing_base_uom: bool = False,
    fix_missing_defaults: bool = False,
    dry_run: bool = True,
) -> NormalizeResult:
    result = NormalizeResult(dry_run=dry_run)

    enabled: Dict[str, List[str]] = {}
    if do_each:
        enabled["Each"] = CANONICAL_MAP["Each"]
    if do_sht:
        enabled["Sht"] = CANONICAL_MAP["Sht"]

    if not enabled and not fix_missing_base_uom and not fix_missing_defaults:
        result.errors.append("No normalization/fix options selected.")
        return result

    # Resolve ids for alias normalization
    rows: List[NormalizeRow] = []
    for canonical, aliases in enabled.items():
        row = NormalizeRow(canonical_name=canonical, alias_names=list(aliases))

        canonical_obj = _get_measurement_by_name(canonical)
        if not canonical_obj:
            row.notes.append(f"Missing canonical Measurement named '{canonical}'.")
            result.errors.append(f"Missing canonical Measurement named '{canonical}'.")
            rows.append(row)
            continue

        row.canonical_id = canonical_obj.id

        alias_ids: List[int] = []
        for a in aliases:
            ao = _get_measurement_by_name(a)
            if ao:
                alias_ids.append(ao.id)

        row.alias_ids = sorted(set(alias_ids))
        if not row.alias_ids:
            row.notes.append(f"No alias Measurements found for {aliases}. Nothing to do.")

        rows.append(row)

    result.rows = rows
    if result.errors:
        return result

    item_ids = list(item_qs.values_list("id", flat=True))
    result.matched_items = len(item_ids)

    # -----------------------------
    # 1) Normalize variation FK
    # -----------------------------
    for row in result.rows:
        if not row.alias_ids:
            continue

        var_qs = InventoryQtyVariations.objects.filter(
            inventory_id__in=item_ids,
            variation_id__in=row.alias_ids,
        )
        row.matched_variations = var_qs.count()

        if not dry_run and row.matched_variations:
            row.changed_variations = var_qs.update(variation_id=row.canonical_id)
        else:
            row.changed_variations = row.matched_variations

    # -----------------------------
    # 2) Normalize primary_base_unit
    # -----------------------------
    if include_primary_base_unit:
        for row in result.rows:
            if not row.alias_ids:
                continue

            base_qs = InventoryMaster.objects.filter(
                id__in=item_ids,
                primary_base_unit_id__in=row.alias_ids,
            )
            row.matched_primary_base_units = base_qs.count()

            if not dry_run and row.matched_primary_base_units:
                row.changed_primary_base_units = base_qs.update(primary_base_unit_id=row.canonical_id)
            else:
                row.changed_primary_base_units = row.matched_primary_base_units

    # -----------------------------
    # 3) Fix missing base/defaults (guarded)
    # -----------------------------
    each = _get_measurement_by_name("Each")  # used as safe default base
    if (fix_missing_base_uom or fix_missing_defaults) and not each:
        result.errors.append("Missing Measurement 'Each' (required for fixes).")
        return result

    # summary counters (your template expects these)
    result.missing_base_items = 0
    result.base_set_items = 0
    result.missing_default_sell_items = 0
    result.default_sell_set_items = 0
    result.missing_default_receive_items = 0
    result.default_receive_set_items = 0

    if fix_missing_base_uom or fix_missing_defaults:
        items = (
            InventoryMaster.objects
            .filter(id__in=item_ids)
            .prefetch_related("variations")
        )

        for item in items:
            vars_list = list(item.variations.all())
            base = next((v for v in vars_list if v.is_base_unit and v.active), None)
            has_base_flag_any = any(v.is_base_unit for v in vars_list)

            if fix_missing_base_uom:
                if base is None:
                    result.missing_base_items += 1

                    if not dry_run:
                        # if there are any base flags but none active, don't guess—skip
                        if has_base_flag_any:
                            continue

                        # create (or reuse) Each×1 variation as base
                        v, _ = InventoryQtyVariations.objects.get_or_create(
                            inventory=item,
                            variation=each,
                            variation_qty=Decimal("1.0000"),
                            defaults={"active": True},
                        )
                        # clear any old base flags just in case
                        InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True).exclude(pk=v.pk).update(is_base_unit=False)
                        if not v.is_base_unit or not v.active:
                            v.is_base_unit = True
                            v.active = True
                            v.save(update_fields=["is_base_unit", "active"])
                    result.base_set_items += 1

            # refresh base pointer (for defaults)
            if base is None:
                vars_list = list(item.variations.all())
                base = next((v for v in vars_list if v.is_base_unit and v.active), None)

            if fix_missing_defaults and base is not None:
                if item.retail:
                    has_sell = any(v.is_default_sell_uom and v.active for v in vars_list)
                    if not has_sell:
                        result.missing_default_sell_items += 1
                        if not dry_run:
                            InventoryQtyVariations.objects.filter(inventory=item, is_default_sell_uom=True).exclude(pk=base.pk).update(is_default_sell_uom=False)
                            if not base.is_default_sell_uom:
                                base.is_default_sell_uom = True
                                base.save(update_fields=["is_default_sell_uom"])
                        result.default_sell_set_items += 1

                if item.supplies:
                    has_recv = any(v.is_default_receive_uom and v.active for v in vars_list)
                    if not has_recv:
                        result.missing_default_receive_items += 1
                        if not dry_run:
                            InventoryQtyVariations.objects.filter(inventory=item, is_default_receive_uom=True).exclude(pk=base.pk).update(is_default_receive_uom=False)
                            if not base.is_default_receive_uom:
                                base.is_default_receive_uom = True
                                base.save(update_fields=["is_default_receive_uom"])
                        result.default_receive_set_items += 1

    return result