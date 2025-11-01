import pytest
from inventory.models import InventoryPricingGroup

@pytest.mark.django_db
def test_add_to_price_group_idempotent(master, group):
    # call model helper (should create through row once)
    master.add_to_price_group(group)
    master.add_to_price_group(group)

    assert InventoryPricingGroup.objects.filter(inventory=master, group=group).count() == 1
    # the M2M should reflect it too
    assert master.price_group.filter(pk=group.pk).exists()