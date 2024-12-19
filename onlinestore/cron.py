from django.db.models import Max
from inventory.models import InventoryMaster
from finance.models import InvoiceItem



def high_price_item():
    items = InventoryMaster.objects.filter().exclude(non_inventory=1)
    for x in items:
        try:
            high_cost = InvoiceItem.objects.filter(internal_part_number=x.pk).aggregate(Max('unit_cost'))
            high_cost = list(high_cost.values())[0]
        except:
            high_cost = None
        if high_cost:
            InventoryMaster.objects.filter(pk=x.pk).update(high_price=high_cost)
            # Workorder.objects.filter(pk=x.pk).update(checked_and_verified=1)