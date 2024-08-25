from django.db import models
from django.urls import reverse
from datetime import datetime
from django.db.models import Max
from inventory.models import Vendor, InventoryMaster, VendorItemDetail
from workorders.models import Workorder
from controls.models import PaymentType
from customers.models import Customer

from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    #post_delete
)


class AccountsPayable(models.Model):
    invoice_date = models.DateField(auto_now=False, auto_now_add=False)
    vendor = models.ForeignKey(Vendor, blank=False, null=False, on_delete=models.DO_NOTHING)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    total = models.CharField('Total', max_length=100, blank=True, null=True)
    invoice_number = models.CharField('Invoice Number', max_length=100, blank=True, null=False)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2, blank=True, null=True)
    date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    discount = models.DecimalField('Discount', blank=True, null=True, max_digits=10, decimal_places=2)
    discount_date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    paid = models.BooleanField('Paid', null=True, default=False)
    date_paid = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    amount_paid = models.DecimalField('Amount Paid', blank=True, null=True, max_digits=10, decimal_places=2)
    payment_method = models.CharField('Payment Method', choices=[('Cash', 'Cash'), ('Check', 'Check'), ('Credit Card', 'Credit Card'), ('Trade', 'Trade'), ('Other', 'Other')], max_length=100, blank=True, null=True)
    retail_invoice = models.BooleanField('Retail Invoice', null=True, default=True)
    supplies_invoice = models.BooleanField('Supplies Invoice', null=True, default=True)
    order_out = models.BooleanField('Order Out', null=True, default=True)
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
    date= models.DateField(auto_now=True, auto_now_add=False, blank=False, null=False)
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
    
class Appliedother(models.Model):
    date= models.DateField(auto_now=False, auto_now_add=False, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=False, null=False, on_delete=models.DO_NOTHING)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2, blank=True, null=True)
    memo = models.CharField('Memo', max_length=500, blank=True, null=True)


    def __str__(self):
        return self.customer.company_name
    
class InvoiceItem(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(AccountsPayable, blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField('Qty', max_digits=8, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)    

    def __str__(self):
        return self.name
    


@receiver(post_save, sender=InvoiceItem)   
def highprice_handler(sender, instance, created, *args, **kwargs):
    print(args, kwargs)
    print('cool')
    internal_part_number = instance.internal_part_number
    unit_cost = instance.unit_cost
    vendor = instance.vendor.id
    print(instance.unit_cost)
    print(instance.vendor.id)
    name = instance.name
    print(name)
    vendor_part_number = instance.vendor_part_number
    print(vendor_part_number)
    description = instance.description
    print(description)
    items = InvoiceItem.objects.filter(vendor=vendor, internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
    print(items)
    price = list(items.values())[0]
    #price_dec = 
    #Update high price for vendor item
    current_high = VendorItemDetail.objects.get(vendor=vendor, internal_part_number=internal_part_number)
    current_high = current_high.high_price
    if current_high is None:
        current_high = 0
    if price is None:
        price = 0
    print(current_high)
    if current_high < price:
        print('ok')
        VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(high_price=price, updated=datetime.now())
    else:
        print('no change')
    #price = items
    print(price)
    #This line is broken
    #VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(name=name, vendor_part_number=vendor_part_number, description=description, updated=datetime.now())
    print('done')
    #items = RetailInvoiceItem.objects.filter(vendor=vendor, internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
    # for x in items:
    #     print (x.name)
    #     print (x.unit_cost)

#post_save.connect(highprice_handler, sender=InvoiceItem)

# @receiver(post_delete, sender=InvoiceItem)   
# def highprice_handler(sender, instance, *args, **kwargs):
#     print('deleted')
#     print(instance)
#     print(instance.vendor)
#     vendor = instance.vendor.id
#     internal_part_number = instance.internal_part_number
#     print(internal_part_number)
#     items = InvoiceItem.objects.filter(vendor=vendor, internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
#     print(items)
#     price = list(items.values())[0]
#     print(price)
#     VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(high_price=price, updated=datetime.now())
    