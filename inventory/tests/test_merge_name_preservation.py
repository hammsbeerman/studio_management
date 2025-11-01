import pytest
from inventory.models import InventoryMaster
from inventory.services import merge_inventory_items

@pytest.mark.django_db
def test_prefer_target_name_flag_controls_name_borrowing():
    t = InventoryMaster.objects.create(name="Target")
    d = InventoryMaster.objects.create(name="Donor Name")

    # default (prefer_target_name=True) keeps target's name
    merge_inventory_items(t, [d], user=None, prefer_target_name=True)
    t.refresh_from_db()
    assert t.name == "Target"

@pytest.mark.django_db
def test_can_borrow_name_when_target_blank():
    t = InventoryMaster.objects.create(name="")
    d = InventoryMaster.objects.create(name="Better Name")
    merge_inventory_items(t, [d], user=None, prefer_target_name=False)
    t.refresh_from_db()
    assert t.name == "Better Name"