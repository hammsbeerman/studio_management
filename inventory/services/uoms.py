from __future__ import annotations

from django.db import transaction

from inventory.models import InventoryMaster, InventoryQtyVariations
from controls.models import Measurement


@transaction.atomic
def ensure_base_uom(*, item: InventoryMaster, measurement: Measurement, activate: bool = True) -> InventoryQtyVariations:
    """Ensure exactly one base UOM row is flagged for the item.

    Notes:
      - We *do not* assume only one row per measurement.
      - We prefer qty==1 if present for the measurement, otherwise smallest qty.
      - If no rows exist for measurement, create qty==1.
    """
    qs = InventoryQtyVariations.objects.select_for_update().filter(inventory=item, variation=measurement)

    # pick candidate
    base_row = qs.filter(variation_qty=1).order_by("id").first() or qs.order_by("variation_qty", "id").first()
    if base_row is None:
        base_row = InventoryQtyVariations.objects.create(
            inventory=item,
            variation=measurement,
            variation_qty=1,
            **({"active": True} if hasattr(InventoryQtyVariations, "active") and activate else {}),
        )
    else:
        if activate and hasattr(base_row, "active") and base_row.active is False:
            base_row.active = True
            base_row.save(update_fields=["active"])

    # clear other base flags
    if hasattr(InventoryQtyVariations, "is_base_unit"):
        InventoryQtyVariations.objects.filter(inventory=item, is_base_unit=True).exclude(pk=base_row.pk).update(is_base_unit=False)
        if base_row.is_base_unit is False:
            base_row.is_base_unit = True
            base_row.save(update_fields=["is_base_unit"])

    # keep InventoryMaster.primary_base_unit in sync
    if getattr(item, "primary_base_unit_id", None) != measurement.id:
        item.primary_base_unit = measurement
        item.save(update_fields=["primary_base_unit"])

    return base_row


@transaction.atomic
def set_default_sell_uom(*, item: InventoryMaster, uom: InventoryQtyVariations) -> None:
    if not hasattr(InventoryQtyVariations, "is_default_sell_uom"):
        return

    InventoryQtyVariations.objects.select_for_update().filter(inventory=item, is_default_sell_uom=True).exclude(pk=uom.pk).update(
        is_default_sell_uom=False
    )
    if uom.is_default_sell_uom is False:
        uom.is_default_sell_uom = True
        uom.save(update_fields=["is_default_sell_uom"])


@transaction.atomic
def set_default_receive_uom(*, item: InventoryMaster, uom: InventoryQtyVariations) -> None:
    if not hasattr(InventoryQtyVariations, "is_default_receive_uom"):
        return

    InventoryQtyVariations.objects.select_for_update().filter(inventory=item, is_default_receive_uom=True).exclude(pk=uom.pk).update(
        is_default_receive_uom=False
    )
    if uom.is_default_receive_uom is False:
        uom.is_default_receive_uom = True
        uom.save(update_fields=["is_default_receive_uom"])