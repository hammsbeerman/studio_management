from django.db import models
from inventory.models import InventoryMaster

from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    post_delete
)

class StoreItemDetails(models.Model):
    item = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False) 
    high_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=5, blank=True, null=True)
    online_store_price = models.DecimalField('Online Store Price', max_digits=15, decimal_places=5, blank=True, null=True)
    retail_store_price = models.DecimalField('Retail Store Price', max_digits=15, decimal_places=5, blank=True, null=True)
    oneforty_percent = models.DecimalField('140 Percent Markup', max_digits=15, decimal_places=5, blank=True, null=True)
    actual_markup = models.DecimalField('Actual Markup', max_digits=15, decimal_places=5, blank=True, null=True)
    date_last_price_change = models.DateTimeField(auto_now = False, blank=True, null=True)
   

    def __str__(self):
            return self.item.name
    

class StoreItemVariation(models.Model):
      item = models.ForeignKey(StoreItemDetails, on_delete=models.CASCADE)
      var_name = models.CharField('Name', max_length=100, blank=False, null=False)
      var_qty = models.DecimalField('Variation Qty', max_digits=15, decimal_places=5, blank=True, null=True)
      var_online_price = models.DecimalField('Online Store Price', max_digits=15, decimal_places=5, blank=True, null=True)
      var_multiplier = models.DecimalField('Multiplier from Base Unit', max_digits=15, decimal_places=5, blank=True, null=True)
      var_markup = models.DecimalField('Markup', max_digits=15, decimal_places=5, blank=True, null=True)

class StoreItemDetailHistory(models.Model):
    item = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False) 
    online_store_price = models.DecimalField('Online Store Price', max_digits=15, decimal_places=5, blank=True, null=True)
    retail_store_price = models.DecimalField('Retail Store Price', max_digits=15, decimal_places=5, blank=True, null=True)
    date_last_price_change = models.DateTimeField(auto_now = False, blank=True, null=True)

    
    
# @receiver(post_save, sender=StoreItemDetails)   
# def markup_handler(sender, instance, created, *args, **kwargs):
#       high_cost = instance.high_cost
#       current_price = instance.online_store_price
#       if not high_cost:
#             high_cost = 0
#       oneforty = high_cost * 1.4
#       print('actual')
#       try:
#            actual = current_price / high_cost
#            actual = actual * 100
#            print('actual')
#            print(actual)
#       except:
#            actual = '0'
#       StoreItemDetails.objects.filter(pk=instance.pk).update(oneforty_percent=oneforty, actual_markup=actual)

class StoreItemPricing(models.Model):
      item = models.ForeignKey(StoreItemDetails, on_delete=models.CASCADE)

