import pytest
from inventory.models import InventoryMaster, InventoryPricingGroup
from controls.models import GroupCategory

@pytest.mark.django_db
def test_price_group_through_fields_and_related_names():
    item = InventoryMaster.objects.create(name="Item")
    g = GroupCategory.objects.create(name="C1")

    # create via through
    link = InventoryPricingGroup.objects.create(inventory=item, group=g)

    # access from item -> groups (M2M)
    groups = list(item.price_group.all())
    assert g in groups

    # access from group -> items (related_name='items')
    items = list(g.items.all())
    assert item in items

    # access through reverse managers (related_name on FKs)
    assert list(item.pricing_group_links.all()) == [link]
    assert list(g.item_links.all()) == [link]