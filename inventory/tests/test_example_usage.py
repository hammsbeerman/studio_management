from inventory.tests.factories import (
    InventoryMasterFactory,
    InventoryPricingGroupFactory,
    GroupCategoryFactory,
    WorkorderItemFactory,
)

def test_example(db):
    item = InventoryMasterFactory()
    g = GroupCategoryFactory()
    InventoryPricingGroupFactory(inventory=item, group=g)
    assert item.price_group.filter(pk=g.pk).exists()