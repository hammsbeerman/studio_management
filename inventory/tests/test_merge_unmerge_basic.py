import pytest
from django.db import IntegrityError
from django.utils import timezone

from inventory.models import (
    InventoryMaster,
    InventoryPricingGroup,
    InventoryMergeLog,
)
from controls.models import GroupCategory
# If your WorkorderItem lives in another app, adjust this import:
from workorders.models import WorkorderItem

# Services under test
from inventory.services import merge_inventory_items, unmerge_inventory_items


@pytest.mark.django_db
def test_merge_moves_fk_history_and_soft_deletes(user_factory):
    # Arrange: target + dup
    target = InventoryMaster.objects.create(name="Target", is_active=True)
    dup = InventoryMaster.objects.create(name="Dup", is_active=True)

    # A FK row pointing at dup (will be retargeted)
    wo_dup = WorkorderItem.objects.create(inventory_item=dup, qty=3)

    # A price group on dup via through
    g1 = GroupCategory.objects.create(name="Group A")
    InventoryPricingGroup.objects.create(inventory=dup, group=g1)

    # Act: merge dup -> target
    log = merge_inventory_items(target=target, dups=[dup], user=None, prefer_target_name=True)

    # Assert: soft-deleted + merged_into set
    dup.refresh_from_db()
    assert dup.is_active is False
    assert dup.merged_into_id == target.id

    # Assert: FK retargeted
    wo_dup.refresh_from_db()
    assert wo_dup.inventory_item_id == target.id

    # Assert: through rows reassigned to target
    assert InventoryPricingGroup.objects.filter(inventory=target, group=g1).exists()
    # and no stray link remains on dup
    assert not InventoryPricingGroup.objects.filter(inventory=dup, group=g1).exists()

    # Assert: merge log created with dup id captured
    assert isinstance(log, InventoryMergeLog)
    assert dup.id in log.merged_ids


@pytest.mark.django_db
def test_unmerge_restores_everything(user_factory):
    # Arrange
    target = InventoryMaster.objects.create(name="Target", is_active=True)
    dup = InventoryMaster.objects.create(name="Dup", is_active=True)
    g = GroupCategory.objects.create(name="Group X")
    InventoryPricingGroup.objects.create(inventory=dup, group=g)
    wo_dup = WorkorderItem.objects.create(inventory_item=dup, qty=1)

    # Merge
    log = merge_inventory_items(target, [dup], user=None)

    # Sanity: post-merge state
    dup.refresh_from_db()
    assert dup.is_active is False
    assert WorkorderItem.objects.get(pk=wo_dup.pk).inventory_item_id == target.id
    assert InventoryPricingGroup.objects.filter(inventory=target, group=g).exists()

    # Act: UNMERGE
    out = unmerge_inventory_items(log.pk, user=None)
    assert dup.id in out["restored_items"]

    # Assert: original state restored
    dup.refresh_from_db()
    assert dup.is_active is True
    assert dup.merged_into_id is None

    wo_dup.refresh_from_db()
    assert wo_dup.inventory_item_id == dup.id

    assert InventoryPricingGroup.objects.filter(inventory=dup, group=g).exists()
    assert not InventoryPricingGroup.objects.filter(inventory=target, group=g).exists()


@pytest.mark.django_db
def test_merge_log_tracks_multiple_dups(user_factory):
    t = InventoryMaster.objects.create(name="T")
    d1 = InventoryMaster.objects.create(name="D1")
    d2 = InventoryMaster.objects.create(name="D2")
    log = merge_inventory_items(t, [d1, d2], user=None)
    assert set(log.merged_ids) == {d1.id, d2.id}


@pytest.mark.django_db
def test_inventory_pricing_group_unique_constraint():
    item = InventoryMaster.objects.create(name="Item")
    g = GroupCategory.objects.create(name="Group")
    InventoryPricingGroup.objects.create(inventory=item, group=g)
    # duplicate pair should violate unique constraint
    with pytest.raises(IntegrityError):
        InventoryPricingGroup.objects.create(inventory=item, group=g)