import pytest
from inventory.models import Vendor, VendorItem, PriceHistory, PurchaseLine, InventoryMaster
from inventory.services import merge_inventory_items
from workorders.models import WorkorderItem

@pytest.mark.django_db
def test_merge_moves_relations():
    target = InventoryMaster.objects.create(name="A")
    dup = InventoryMaster.objects.create(name="A 2")
    v = Vendor.objects.create(name="Acme")
    VendorItem.objects.create(item=dup, vendor=v, vendor_sku="X1", current_price=5)
    PriceHistory.objects.create(item=dup, vendor=v, price=4, effective_date="2024-01-01")
    PurchaseLine.objects.create(item=dup, vendor=v, qty=10, unit_price=5)
    WorkorderItem.objects.create(inventory_item=dup, qty=2)

    merge_inventory_items(target, [dup], user=None)

    dup.refresh_from_db()
    assert dup.is_active is False
    assert dup.merged_into_id == target.id
    assert VendorItem.objects.filter(item=target, vendor=v).exists()
    assert PriceHistory.objects.filter(item=target).count() == 1
    assert PurchaseLine.objects.filter(item=target).count() == 1
    assert WorkorderItem.objects.filter(inventory_item=target).count() == 1