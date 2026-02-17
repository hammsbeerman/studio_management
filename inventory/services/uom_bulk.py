from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.db import transaction
from django.db.models import Q

from inventory.models import InventoryMaster, InventoryQtyVariations, Measurement


@dataclass
class BulkUomResult:
    matched: int
    changed: int
    created: int
    skipped: int


def _get_or_create_variation(
    item: InventoryMaster,
    measurement: Measurement,
    variation_qty: Decimal,
) -> tuple[InventoryQtyVariations, bool]:
    v = InventoryQtyVariations.objects.filter(
        inventory=item,
        variation=measurement,
        variation_qty=variation_qty,
    ).first()
    if v:
        return v, False

    v = InventoryQtyVariations.objects.create(
        inventory=item,
        variation=measurement,
        variation_qty=variation_qty,
        active=True,
    )
    return v, True


@transaction.atomic
def bulk_set_item_uom(
    *,
    item_qs,
    measurement: Measurement,
    variation_qty: Decimal = Decimal("1.0000"),
    set_as_base: bool = False,
    set_as_default_sell: bool = False,
    set_as_default_receive: bool = False,
    dry_run: bool = True,
) -> BulkUomResult:
    matched = item_qs.count()
    changed = created = skipped = 0

    # lock rows so two admins don’t step on each other
    items = list(item_qs.select_for_update())

    for item in items:
        # ensure variation exists
        v, did_create = _get_or_create_variation(item, measurement, variation_qty)

        # decide what would change
        would_change = False

        if set_as_base and not v.is_base_unit:
            would_change = True
        if set_as_default_sell and not v.is_default_sell_uom:
            would_change = True
        if set_as_default_receive and not v.is_default_receive_uom:
            would_change = True

        if not would_change and not did_create:
            skipped += 1
            continue

        if dry_run:
            # don’t touch DB in dry-run
            created += 1 if did_create else 0
            changed += 1 if would_change else 0
            continue

        # apply updates
        if did_create:
            created += 1

        # IMPORTANT: clear existing flags if setting defaults/base
        if set_as_base:
            InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True).update(is_base_unit=False)
            v.is_base_unit = True

        if set_as_default_sell:
            InventoryQtyVariations.objects.filter(inventory=item, is_default_sell_uom=True).update(is_default_sell_uom=False)
            v.is_default_sell_uom = True

        if set_as_default_receive:
            InventoryQtyVariations.objects.filter(inventory=item, is_default_receive_uom=True).update(is_default_receive_uom=False)
            v.is_default_receive_uom = True

        v.active = True
        v.save()

        changed += 1

    return BulkUomResult(matched=matched, changed=changed, created=created, skipped=skipped)


def build_item_queryset(
    *,
    only_active: bool = True,
    name_contains: str = "",
    vendor_id: Optional[int] = None,
) :
    qs = InventoryMaster.objects.all()
    if only_active:
        qs = qs.filter(active=True)
    if name_contains:
        qs = qs.filter(Q(name__icontains=name_contains) | Q(description__icontains=name_contains))
    if vendor_id:
        qs = qs.filter(primary_vendor_id=vendor_id)
    return qs