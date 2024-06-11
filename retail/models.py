from django.db import models
from controls.models import RetailInventoryCategory
from inventory.models import Inventory

class PriceBreaks(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    qty_full_price = models.DecimalField('Full Price Qty', max_digits=10, decimal_places=2, blank=True, null=True)
    full_price_pct = models.DecimalField('Full Price Pct', max_digits=10, decimal_places=2, blank=True, null=True)
    qty_break_one = models.DecimalField('Break 1 Qty', max_digits=10, decimal_places=2, blank=True, null=True)
    break_one_pct = models.DecimalField('Break 1 Pct', max_digits=10, decimal_places=2, blank=True, null=True)
    qty_break_two = models.DecimalField('Break 2 Qty', max_digits=10, decimal_places=2, blank=True, null=True)
    break_two_pct = models.DecimalField('Break 2 Pct', max_digits=10, decimal_places=2, blank=True, null=True)

class OfficeSupplies(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)


class RetailInventory(models.Model):
    paper_item = models.ForeignKey(Inventory, blank=True, null=True, on_delete=models.DO_NOTHING)
    office_supply_item = models.ForeignKey(OfficeSupplies, blank=True, null=True, on_delete=models.DO_NOTHING)
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2, blank=True, null=True)
    qty_on_hand = models.DecimalField('Qty on Hand', max_digits=10, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    inventory_category = models.ManyToManyField(RetailInventoryCategory)
    # purchase_price = 
    # sell_price = 
    # sale_price = 
    # on_sale = 

    def __str__(self):
        return self.item.name



