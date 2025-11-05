from typing import Iterable, Set
from django.db.models import Q
from .models import InventoryMaster, InventoryMerge

def merged_set_for(item: InventoryMaster) -> Set[int]:
    """All item IDs that should contribute to 'item' history: itself + merged-in dupes."""
    ids = {item.id}
    # one-level (simple) merges
    dupes = InventoryMerge.objects.filter(to_item=item).values_list("from_item_id", flat=True)
    ids.update(dupes)
    return ids