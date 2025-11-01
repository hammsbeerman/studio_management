from django.db.models.signals import post_save, pre_save
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.dispatch import receiver
from .models import InventoryMaster, Inventory
from decimal import Decimal
#from .utils import q

def _q(val, fmt: str):
    """Quantize helper (ROUND_HALF_UP). Accepts Decimal/str/number; returns Decimal."""
    if val is None:
        return None
    return Decimal(val).quantize(Decimal(fmt), rounding=ROUND_HALF_UP)

def q(val, fmt):
    return Decimal(val).quantize(Decimal(fmt), rounding=ROUND_HALF_UP)

@receiver(post_save, sender=InventoryMaster)
def sync_shadow_inventory(sender, instance: InventoryMaster, **kwargs):
    # Compute unit_cost / price_per_m if possible
    unit_cost = price_per_m = None
    if instance.units_per_base_unit and instance.high_price:
        unit_cost = (Decimal(instance.high_price) / Decimal(instance.units_per_base_unit))
        price_per_m = unit_cost * Decimal("1000")

    # Upsert shadow row safely (no manual save with update_fields on new rows)
    # fetch-or-create, but dedupe if somehow multiple exist
    qs = Inventory.objects.filter(internal_part_number=instance).order_by("pk")
    if qs.exists():
        inv = qs.first()
        # delete any accidental duplicates
        if qs.count() > 1:
            qs.exclude(pk=inv.pk).delete()
    else:
        inv = Inventory(internal_part_number=instance)

    inv.name = instance.name or f"Inventory #{instance.pk}"
    inv.retail_item = bool(instance.retail)
    inv.unit_cost = q(unit_cost, "0.0000") if unit_cost is not None else None
    inv.price_per_m = q(price_per_m, "0.0000") if price_per_m is not None else None
    inv.save()

# @receiver(post_save, sender=InventoryMaster)
# def sync_shadow_inventory(sender, instance: InventoryMaster, **kwargs):
#     # Compute from Decimals (never floats)
#     unit_cost = price_per_m = None
#     if instance.units_per_base_unit and instance.high_price:
#         hp = Decimal(instance.high_price)
#         upbu = Decimal(instance.units_per_base_unit)
#         unit_cost = hp / upbu
#         price_per_m = unit_cost * Decimal(1000)
#     else:
#         unit_cost = None
#         price_per_m = None

#     # Persist computed fields on master (6 dp as per tests), using UPDATE to avoid signal recursion
#     changed = {}
#     if unit_cost is not None:
#         uc6 = q(unit_cost, "0.000000")
#         if instance.unit_cost != uc6:
#             changed["unit_cost"] = uc6
#             instance.unit_cost = uc6
#     if price_per_m is not None:
#         ppm6 = q(price_per_m, "0.000000")
#         if instance.price_per_m != ppm6:
#             changed["price_per_m"] = ppm6
#             instance.price_per_m = ppm6
#     if changed:
#         InventoryMaster.objects.filter(pk=instance.pk).update(**changed)

#     # Upsert shadow Inventory (4 dp), tolerating historical duplicates
#     inv = Inventory.objects.filter(internal_part_number=instance).first()
#     if inv is None:
#         inv = Inventory(internal_part_number=instance)

#     inv.name = instance.name
#     inv.retail_item = bool(instance.retail)
#     inv.unit_cost = _q(unit_cost,  "0.0000") if unit_cost is not None else None
#     inv.price_per_m = _q(price_per_m, "0.0000") if price_per_m is not None else None
#     inv.save(update_fields=["name", "retail_item", "unit_cost", "price_per_m"])

def _recompute_master_costs(instance: InventoryMaster) -> dict:
    """
    Compute unit_cost and price_per_m (per thousand) from high_price/units_per_base_unit.
    Returns dict of field updates to apply. Leaves values alone if inputs missing.
    """
    updates = {}
    if instance.high_price is not None and instance.units_per_base_unit:
        try:
            unit_cost = (Decimal(instance.high_price) / Decimal(instance.units_per_base_unit)).quantize(Decimal("0.000001"))
            price_per_m = (unit_cost * Decimal(1000)).quantize(Decimal("0.000001"))
        except (ArithmeticError, ValueError):
            unit_cost = None
            price_per_m = None

        # Only update when changed/None to avoid loops
        if instance.unit_cost != unit_cost:
            updates["unit_cost"] = unit_cost
        if instance.price_per_m != price_per_m:
            updates["price_per_m"] = price_per_m
    return updates

@receiver(pre_save, sender=InventoryMaster)
def compute_prices(sender, instance: InventoryMaster, **kwargs):
    """
    Compute unit_cost (6 dp) and price_per_m (6 dp) on the master record.
    Always use Decimal to avoid float math.
    """
    if instance.high_price is not None and instance.units_per_base_unit:
        # Force Decimal, even if a float slipped in from a factory/test
        hp = Decimal(str(instance.high_price))
        upbu = Decimal(str(instance.units_per_base_unit))

        unit_cost = (hp / upbu).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        price_per_m = unit_cost * Decimal(1000)

        instance.unit_cost = q(unit_cost, "0.000001")
        instance.price_per_m = q(price_per_m, "0.000001")
    else:
        # Leave fields alone or set to None—pick the behavior you want.
        instance.unit_cost = None
        instance.price_per_m = None

@receiver(post_save, sender=InventoryMaster)
def ensure_child_inventory(sender, instance: InventoryMaster, created=False, raw=False, **kwargs):
    """
    Guarantee exactly one Inventory row per InventoryMaster.
    - If none exists, create one.
    - If multiple exist (historical/accidental), keep the oldest and delete the rest.
    - Keep the child name in sync with the master (but never create by name).
    """
    if raw:
        # Skip when loading fixtures or certain migration contexts.
        return
    from inventory.models import Inventory
    
    # 1) recompute master pricing (without re-triggering signals)
    master_updates = _recompute_master_costs(instance)
    if master_updates:
        master_updates["updated"] = timezone.now()
        InventoryMaster.objects.filter(pk=instance.pk).update(**master_updates)

    # 2) sync / create child inventory row
    qs = Inventory.objects.filter(internal_part_number=instance).order_by("pk")
    inv = qs.first()

    # if not qs.exists():
    #     inv = Inventory.objects.create(internal_part_number=instance, name=instance.name)
    #     return

    # inv = qs.first()

    if not inv:
        Inventory.objects.create(
            internal_part_number=instance,
            name=instance.name or "",
            description=(instance.description or ""),
            measurement=instance.primary_base_unit,
            retail_item=instance.retail,
            unit_cost=instance.unit_cost,
            price_per_m=instance.price_per_m,
        )
        return
    
    # update a minimal set of fields
    updates = {}
    if inv.name != (instance.name or ""):
        updates["name"] = instance.name or ""
    if (inv.description or "") != (instance.description or ""):
        updates["description"] = instance.description or ""
    if inv.measurement_id != instance.primary_base_unit_id:
        updates["measurement_id"] = instance.primary_base_unit_id
    if inv.retail_item != instance.retail:
        updates["retail_item"] = instance.retail
    # don't clobber child prices unless master is authoritative
    if inv.unit_cost is None and instance.unit_cost is not None:
        updates["unit_cost"] = instance.unit_cost
    if inv.price_per_m is None and instance.price_per_m is not None:
        updates["price_per_m"] = instance.price_per_m

    if updates:
        updates["updated"] = timezone.now()
        Inventory.objects.filter(pk=inv.pk).update(**updates)

    # Clean up accidental duplicates (idempotent)
    extras = qs.exclude(pk=inv.pk)
    if extras.exists():
        extras.delete()

    # Keep the canonical child name in sync
    if inv.name != instance.name:
        inv.name = instance.name
        inv.save(update_fields=["name"])