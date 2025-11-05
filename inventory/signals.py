from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from .models import InventoryMaster, Inventory, GroupCategory

def _q(val, places="0.000001"):
    """
    Quantize Decimal with HALF_UP. places default = 6 decimal places.
    """
    if val is None:
        return None
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(Decimal(places), rounding=ROUND_HALF_UP)

# --- 1) Keep unit_cost / price_per_m in sync on InventoryMaster ---

@receiver(pre_save, sender=InventoryMaster)
def inventory_master_compute_prices(sender, instance: InventoryMaster, **kwargs):
    """
    If we have high_price and units_per_base_unit, compute:
      - unit_cost = high_price / units_per_base_unit  (6 dp)
      - price_per_m = unit_cost * 1000                (6 dp)
    Idempotent: only sets if inputs exist.
    """
    hp = instance.high_price
    upu = instance.units_per_base_unit
    if hp and upu and upu != 0:
        unit_cost = _q(Decimal(hp) / Decimal(upu), "0.000001")
        price_per_m = _q(unit_cost * Decimal(1000), "0.000001")
        instance.unit_cost = unit_cost
        instance.price_per_m = price_per_m
    # always keep updated timestamp consistent
    instance.updated = timezone.now()

# --- 2) Ensure a child Inventory row mirrors key fields (get_or_create) ---

@receiver(post_save, sender=InventoryMaster)
def inventory_master_mirror_child(sender, instance: InventoryMaster, created, **kwargs):
    """
    Make sure there is an Inventory row pointing at this master.
    Do minimal writes, avoid race using on_commit.
    """
    def _ensure_child():
        inv, made = Inventory.objects.get_or_create(
            internal_part_number=instance,
            defaults={
                "name": instance.name,
                "description": instance.description or "",
                "unit_cost": str(instance.unit_cost or ""),
                "price_per_m": str(instance.price_per_m or ""),
                "measurement": instance.primary_base_unit,
                "retail_item": instance.retail,
            },
        )
        # Keep a few fields in sync if changed
        dirty = False
        if inv.name != instance.name:
            inv.name = instance.name; dirty = True
        if (inv.description or "") != (instance.description or ""):
            inv.description = instance.description or ""; dirty = True
        # store as strings because Inventory.unit_cost/price_per_m are CharField
        uc = "" if instance.unit_cost is None else str(_q(instance.unit_cost))
        pm = "" if instance.price_per_m is None else str(_q(instance.price_per_m))
        if (inv.unit_cost or "") != uc:
            inv.unit_cost = uc; dirty = True
        if (inv.price_per_m or "") != pm:
            inv.price_per_m = pm; dirty = True
        if inv.measurement_id != (instance.primary_base_unit_id or inv.measurement_id):
            inv.measurement = instance.primary_base_unit; dirty = True
        if inv.retail_item != bool(instance.retail):
            inv.retail_item = bool(instance.retail); dirty = True
        if dirty:
            inv.updated = timezone.now()
            inv.save(update_fields=["name","description","unit_cost","price_per_m","measurement","retail_item","updated"])
    transaction.on_commit(_ensure_child)

# --- 3) Keep 'grouped' boolean aligned with the M2M price_group ---

@receiver(m2m_changed, sender=InventoryMaster.price_group.through)
def inventory_master_group_flag(sender, instance: InventoryMaster, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        has_groups = instance.price_group.exists()
        if instance.grouped != has_groups:
            instance.grouped = has_groups
            instance.save(update_fields=["grouped"])