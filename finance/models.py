from django.db import models
from django.urls import reverse
from datetime import datetime
from decimal import Decimal
from django.db.models import Max, Sum
from inventory.models import Vendor, InventoryMaster, VendorItemDetail, InventoryPricingGroup, InventoryQtyVariations, Inventory, Measurement
from workorders.models import Workorder
from controls.models import PaymentType
from customers.models import Customer
from onlinestore.models import StoreItemDetails

from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    post_delete
)


class AccountsPayable(models.Model):
    invoice_date = models.DateField(auto_now=False, auto_now_add=False)
    vendor = models.ForeignKey(Vendor, blank=False, null=True, on_delete=models.SET_NULL)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    total = models.CharField('Total', max_length=100, blank=True, null=True)
    calculated_total = models.DecimalField('Calculated Total', max_digits=8, decimal_places=2, blank=True, null=True)
    invoice_number = models.CharField('Invoice Number', max_length=100, blank=True, null=False)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2, blank=True, null=True)
    date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    discount = models.DecimalField('Discount', blank=True, null=True, max_digits=10, decimal_places=2)
    discount_date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    paid = models.BooleanField('Paid', null=True, default=False)
    date_paid = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    amount_paid = models.DecimalField('Amount Paid', blank=True, null=True, max_digits=10, decimal_places=2)
    payment_method = models.CharField('Payment Method', choices=[('Cash', 'Cash'), ('Check', 'Check'), ('Credit Card', 'Credit Card'), ('ACH', 'ACH'), ('Trade', 'Trade'), ('Other', 'Other')], max_length=100, blank=True, null=True)
    check_number = models.CharField('Check Number', max_length=30, blank=True, null=False)
    retail_invoice = models.BooleanField('Retail Invoice', null=True, default=True)
    supplies_invoice = models.BooleanField('Supplies Invoice', null=True, default=True)
    non_inventory = models.BooleanField('Non Inventory Invoice', null=True, default=True)
    order_out = models.BooleanField('Order Out', null=True, default=False)
    #workorder = models.ForeignKey(Workorder, blank=False, null=False, on_delete=models.DO_NOTHING)

    def get_absolute_url(self):
        return reverse("finance:invoice_detail", kwargs={"id": self.id})


    def __str__(self):
        #Pulling from Foreign Key
        return self.vendor.name + ' -- ' + self.invoice_number
    
class DailySales(models.Model):
    date = models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    cash = models.DecimalField('Cash', max_digits=10, decimal_places=2, blank=True, null=True)
    checks = models.DecimalField('Checks', max_digits=10, decimal_places=2, blank=True, null=True)
    creditcard = models.DecimalField('Credit Card', max_digits=10, decimal_places=2, blank=True, null=True)
    creditcard_fee = models.DecimalField('Credit Card Fee', max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        #Formatted this way to convert datetime to string
        return str(self.date)
    
class Payments(models.Model):
    date= models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=False, null=False, on_delete=models.DO_NOTHING)
    workorder = models.ForeignKey(Workorder, blank=True, null=True, on_delete=models.DO_NOTHING, related_name="Workorder")
    payment_type = models.ForeignKey(PaymentType, blank=False, null=False, on_delete=models.DO_NOTHING)
    check_number = models.CharField('Check Number', max_length=100, blank=True, null=True)
    giftcard_number = models.CharField('GiftCard Number', max_length=100, blank=True, null=True)
    refunded_invoice_number = models.CharField('Refund Invoice Number', max_length=100, blank=True, null=True)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2, blank=True, null=True)
    available = models.DecimalField('Amount Available', max_digits=10, decimal_places=2, default=None, null=True)
    memo = models.CharField('Memo', max_length=500, blank=True, null=True)
    void = models.BooleanField('Void Payment', default=False, blank=False, null=False)
    workorder_applied = models.ManyToManyField(Workorder, through='WorkorderPayment')


    def __str__(self):
        return self.customer.company_name + ' -- ' + self.payment_type.name
    
class WorkorderPayment(models.Model):
    workorder = models.ForeignKey(Workorder, null=True, on_delete=models.SET_NULL)
    payment = models.ForeignKey(Payments, null=True, on_delete=models.SET_NULL)
    payment_amount = models.DecimalField('Payment Amount', max_digits=10, decimal_places=2, default=None, null=True)
    date= models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    void = models.BooleanField('Void Payment', default=False, blank=False, null=False)

    def __str__(self):
        return self.workorder.workorder
    
class Araging(models.Model):
    customer = models.OneToOneField(Customer, blank=False, null=True, unique=True, on_delete=models.SET_NULL)
    hr_customer = models.CharField('Customer', max_length=500, blank=True, null=True)
    date = models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    current = models.DecimalField('Current', max_digits=10, decimal_places=2, blank=True, null=True)
    thirty = models.DecimalField('Thirty', max_digits=10, decimal_places=2, blank=True, null=True)
    sixty = models.DecimalField('Sixty', max_digits=10, decimal_places=2, blank=True, null=True)
    ninety = models.DecimalField('Ninety', max_digits=10, decimal_places=2, blank=True, null=True)
    onetwenty = models.DecimalField('One Twenty', max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.customer.company_name
    
class Krueger_Araging(models.Model):
    customer = models.OneToOneField(Customer, blank=False, null=True, unique=True, on_delete=models.SET_NULL)
    hr_customer = models.CharField('Customer', max_length=500, blank=True, null=True)
    date = models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    current = models.DecimalField('Current', max_digits=10, decimal_places=2, blank=True, null=True)
    thirty = models.DecimalField('Thirty', max_digits=10, decimal_places=2, blank=True, null=True)
    sixty = models.DecimalField('Sixty', max_digits=10, decimal_places=2, blank=True, null=True)
    ninety = models.DecimalField('Ninety', max_digits=10, decimal_places=2, blank=True, null=True)
    onetwenty = models.DecimalField('One Twenty', max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.customer.company_name
    
class Appliedother(models.Model):
    date= models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=False, null=False, on_delete=models.DO_NOTHING)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2, blank=True, null=True)
    memo = models.CharField('Memo', max_length=500, blank=True, null=True)


    def __str__(self):
        return self.customer.company_name
    
# class NonInventoryItem(models.Model):
#     name = 
#     description = 

    
class InvoiceItem(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(AccountsPayable, blank=True, null=True, on_delete=models.CASCADE, related_name='invoice')
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name='internal_part_number')
    invoice_unit = models.ForeignKey(InventoryQtyVariations, blank=True, null=True, on_delete=models.CASCADE)
    #invoice_unit = models.CharField('Invoice Unit', max_length=100, blank=True, null=True)
    invoice_unit_cost = models.DecimalField('Invoice Unit Cost', max_digits=15, decimal_places=5, blank=True, null=True)
    invoice_qty = models.DecimalField('Invoice Qty', max_digits=8, decimal_places=2, blank=True, null=True)
    # variation = models.ForeignKey(InventoryQtyVariations, blank=True, null=True, on_delete=models.CASCADE)
    # variation = models.CharField('Variation', max_length=100, blank=True, null=True)
    # variation_name = models.CharField('Description', max_length=100, blank=True, null=True)
    # variation_qty = models.DecimalField('Variation Qty', max_digits=8, decimal_places=2, blank=True, null=True)
    unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=5, blank=True, null=True)
    #price_ea = models.DecimalField('Price Each', max_digits=15, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField('Qty', max_digits=8, decimal_places=2, blank=True, null=True)
    ppm = models.BooleanField('Price Per M', default=False, blank=False, null=False)
    line_total = models.DecimalField('Line Total', max_digits=8, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)    

    def __str__(self):
        return self.name
    
# class AllInvoiceItem(models.Model):
#     invoice_item = models.ForeignKey(InvoiceItem, null=True, on_delete=models.CASCADE)
#     internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
#     invoice_id = models.ForeignKey(AccountsPayable, on_delete=models.CASCADE, null=True, blank=True)
#     #invoice_id = models.IntegerField(null=True, blank=True)
#     purchase_date = models.DateField(auto_now=False, auto_now_add=False)
#     qty = models.DecimalField('Qty', max_digits=8, decimal_places=2, blank=True, null=True)
#     unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
#     vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
#     unit = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
#     line_total = models.DecimalField('Line Total', max_digits=15, decimal_places=4, blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
#     updated = models.DateTimeField(auto_now = True, blank=False, null=False)   

#     def __str__(self):
#         return self.invoice_item.name



# @receiver(post_save, sender=InvoiceItem)
# def all_invoice_items(sender, instance, *args, **kwargs):
#     print('all invoice items')
#     try:
#         AllInvoiceItem.objects.get(invoice_item=instance.pk)
#     except:
#         obj = AllInvoiceItem(invoice_item=InvoiceItem.objects.get(pk=instance.id), invoice_id=instance.id, internal_part_number=InventoryMaster.objects.get(id=instance.internal_part_number.id), purchase_date=instance.invoice.invoice_date, qty=instance.qty, unit_cost=instance.unit_cost, vendor=Vendor.objects.get(pk=instance.vendor.id))
#         #inventory=InventoryMaster.objects.get(pk=pk)
#         obj.save()    

# @receiver(post_save, sender=InvoiceItem)
# def running_total(sender, instance, *args, **kwargs):
#     print('running total')
#     print(instance.invoice.id)
#     total = InvoiceItem.objects.filter(invoice=instance.invoice.id).aggregate(Sum('line_total'))
#     print(total)
#     total = list(total.values())[0]
#     total = Decimal(total)
#     AccountsPayable.objects.filter(pk=instance.invoice.id).update(calculated_total=total)
#     #VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(high_price=price, updated=datetime.now())

#     #total = InvoiceItem.objects.filter(internal_part_number=internal_part_number).aggregate(Max('unit_cost'))

@receiver(post_delete, sender=InvoiceItem)
def running_total(sender, instance, *args, **kwargs):
    print('running total')
    #print(instance.invoice.id)
    try:
        total = InvoiceItem.objects.filter(invoice=instance.invoice.id).aggregate(Sum('line_total'))
        print(total)
        total = list(total.values())[0]
        total = Decimal(total)
        AccountsPayable.objects.filter(pk=instance.invoice.id).update(calculated_total=total)
    except:
        pass



# @receiver(post_delete, sender=InvoiceItem)   
# def highprice_remove_handler(sender, instance, *args, **kwargs):
#     print('highprice_remove_handler')
#     print('deleted')
#     print(instance)
#     print(instance.vendor)
#     vendor = instance.vendor.id
#     internal_part_number = instance.internal_part_number.id
#     print(11)
#     print(internal_part_number)
#     print(vendor)
#     items = InvoiceItem.objects.filter(vendor=vendor, internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
#     print(12)
#     print(items)
#     price = list(items.values())[0]
#     if price:
#         print('1')
#         print(price)
#     else:
#         print('no price')
#     vendorprice = VendorItemDetail.objects.get(vendor=vendor, internal_part_number=internal_part_number)
#     # print('highprice')
#     # print(vendorprice.high_price)
#     #Lower price for vendor item if highest price was deleted from invoice item
#     if vendorprice.high_price > price:
#         VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(high_price=price, updated=datetime.now())
#     #Lower price for inventory master if highest price from any vendor was removed
#     overall_price = InvoiceItem.objects.filter(internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
#     op = list(overall_price.values())[0]
#     master_price = InventoryMaster.objects.get(pk=internal_part_number.id)
#     master_price = master_price.high_price
#     # print('master')
#     # print(master_price)
#     # print('op')
#     # print(op)
#     if master_price > op:
#         m = price * 1000
#         InventoryMaster.objects.filter(pk=internal_part_number.id).update(high_price=price, unit_cost=price, price_per_m=m, updated=datetime.now())
#         try:
#             Inventory.objects.filter(internal_part_number=internal_part_number.id).update(unit_cost=price, price_per_m=m, updated=datetime.now())
#         except:
#             pass
#     # print('hello')
#     groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number.id)
#     # high_price_list = []
#     # list = []
#     high_price_current = 0
#     for x in groups:
#         print('12')
#         #InventoryPricingGroup.objects.filter(group=x.group).update(high_price=price)
#         group_items = InventoryPricingGroup.objects.filter(group=x.group)
#         for x in group_items:
#             # print('13')
#             price = InvoiceItem.objects.filter(internal_part_number=x.inventory.id).aggregate(Max('unit_cost'))
#             price = list(items.values())[0]
#             # print(price)
#             if price > high_price_current:
#                 # print('deleted price')
#                 high_price_current = price
#                 # print(high_price_current)
#             else:
#                 pass
#                 # print(price)
#     price = high_price_current
#     groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number.id)
#     for x in groups:
#         InventoryPricingGroup.objects.filter(group=x.group).update(high_price=price)
#         group_items = InventoryPricingGroup.objects.filter(group=x.group)
#         for x in group_items:
#             y = InventoryMaster.objects.get(pk=x.inventory.id)
#             if y.units_per_base_unit:
#                 cost = price / y.units_per_base_unit
#                 m = cost * 1000
#             else:
#                 cost=0
#                 m = 0
#             # print(x.inventory.id)
#             InventoryMaster.objects.filter(pk=x.inventory.id).update(high_price=price, unit_cost=cost, price_per_m=m, updated=datetime.now())
#             VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=x.inventory.id).update(high_price=price, updated=datetime.now())
#             Inventory.objects.filter(internal_part_number=x.inventory.id).update(unit_cost=cost, price_per_m=m, updated=datetime.now())
#         print(x.inventory)
            
            
#             # InventoryMaster.objects.filter(pk=x.inventory.id).update(high_price=price, unit_cost=cost, price_per_m=m, updated=datetime.now())
#             # VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=x.inventory.id).update(high_price=price, updated=datetime.now())
#             # Inventory.objects.filter(internal_part_number=x.inventory.id).update(unit_cost=cost, price_per_m=m, updated=datetime.now())
#         print(x.inventory)
 

@receiver(post_save, sender=InvoiceItem)   
def highprice_handler(sender, instance, created, *args, **kwargs):
    internal_part_number = instance.internal_part_number
    vendor = instance.vendor.id
    #Check for highprice from specific vendor
    items = InvoiceItem.objects.filter(vendor=vendor, internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
    price = list(items.values())[0]
    print('price')
    print(price)
    current_high = VendorItemDetail.objects.get(vendor=vendor, internal_part_number=internal_part_number)
    current_high = current_high.high_price
    if current_high is None:
        current_high = 0
    if price is None:
        price = 0
    if current_high < price:
        #Update vendor high price
        VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(high_price=price, updated=datetime.now())
        x = InventoryMaster.objects.get(pk=internal_part_number.id)
        if x.units_per_base_unit:
            cost = price / x.units_per_base_unit
            m = cost * 1000
        else:
            cost=0
            m = 0
        InventoryMaster.objects.filter(pk=internal_part_number.id).update(high_price=price, unit_cost=cost, price_per_m=m, updated=datetime.now())
        try:
            Inventory.objects.filter(internal_part_number=internal_part_number.id).update(unit_cost=cost, price_per_m=m, updated=datetime.now())
        except:
            pass
        try:
            StoreItemDetails.objects.filter(item=internal_part_number.id).update(high_cost=price, updated=datetime.now())
        except:
            pass
        groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number.id)
        for x in groups:
            InventoryPricingGroup.objects.filter(group=x.group).update(high_price=price)
            group_items = InventoryPricingGroup.objects.filter(group=x.group)
            for x in group_items:
                print(x.inventory.id)
                InventoryMaster.objects.filter(pk=x.inventory.id).update(high_price=price, unit_cost=cost, price_per_m=m, updated=datetime.now())
                VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=x.inventory.id).update(high_price=price, updated=datetime.now())
                Inventory.objects.filter(internal_part_number=x.inventory.id).update(unit_cost=cost, price_per_m=m, updated=datetime.now())
            print(x.inventory)
    else:
        print('no change')
    print(price)