from django.db import models
from django.urls import reverse
from datetime import datetime
from django.db.models import Max
from controls.models import RetailInventoryCategory, Measurement
from inventory.models import Inventory, Vendor, InventoryMaster, VendorItemDetail
from finance.models import AccountsPayable

# from django.dispatch import receiver
# from django.db.models.signals import (
#     post_save,
#     post_delete
# )
    
    
# class InvoiceItem(models.Model):
#     vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL, related_name="Delete_vendor")
#     invoice = models.ForeignKey(AccountsPayable, blank=True, null=True, on_delete=models.DO_NOTHING, related_name="Delete_invoice")
#     name = models.CharField('Name', max_length=100, blank=False, null=False)
#     vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="Delete_IPN")
#     unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
#     qty = models.DecimalField('Qty', max_digits=8, decimal_places=2, blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
#     updated = models.DateTimeField(auto_now = True, blank=False, null=False)    

#     def __str__(self):
#         return self.name
    
# class InvoiceItem(models.Model):
#     vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
#     invoice = models.ForeignKey(AccountsPayable, blank=True, null=True, on_delete=models.DO_NOTHING)
#     name = models.CharField('Name', max_length=100, blank=False, null=False)
#     vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
#     unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
#     qty = models.DecimalField('Qty', max_digits=8, decimal_places=2, blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
#     updated = models.DateTimeField(auto_now = True, blank=False, null=False)    

#     def __str__(self):
#         return self.name
    










    


    
    




    
    
