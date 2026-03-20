from __future__ import annotations

from decimal import Decimal

from controls.models import Measurement
from inventory.models import InventoryMaster, InventoryQtyVariations


def get_or_create_uom_row(
    *,
    item: InventoryMaster,
    measurement: Measurement,
    qty: Decimal,
    reactivate: bool = True,
) -> InventoryQtyVariations:
    """Single, canonical helper for creating/fetching a UOM row.

    Keyed by (inventory=item, variation=measurement, variation_qty=qty).

    Behavior:
      - Exact active duplicate: reuse
      - Exact inactive duplicate: reactivate (if reactivate=True) and reuse
      - Else: create new row
    """

    qty = Decimal(qty)

    qs = (
        InventoryQtyVariations.objects.filter(
            inventory=item,
            variation=measurement,
            variation_qty=qty,
        )
        .order_by("-id")
    )

    row = qs.first()
    if row:
        if reactivate and hasattr(row, "active") and not row.active:
            row.active = True
            row.save(update_fields=["active"])
        return row

    create_kwargs = {
        "inventory": item,
        "variation": measurement,
        "variation_qty": qty,
    }
    # if the project has the new active flag, default to active
    if "active" in {f.name for f in InventoryQtyVariations._meta.fields}:
        create_kwargs["active"] = True

    return InventoryQtyVariations.objects.create(**create_kwargs)
