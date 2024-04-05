from django.db import models
from inventory.models import Vendor
from workorders.models import Workorder
from controls.models import PaymentType
from customers.models import Customer


class AccountsPayable(models.Model):
    date_recieved = models.DateField(auto_now=False, auto_now_add=False)
    vendor = models.ForeignKey(Vendor, blank=False, null=False, on_delete=models.DO_NOTHING)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    invoice_number = models.CharField('Invoice Number', max_length=100, blank=True, null=True)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Discount', blank=True, null=True, max_digits=10, decimal_places=2)
    discount_date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    paid = models.BooleanField('Paid', null=True, default=False)
    date_paid = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    amount_paid = models.DecimalField('Amount Paid', blank=True, null=True, max_digits=10, decimal_places=2)
    payment_method = models.CharField('Payment Method', choices=[('Cash', 'Cash'), ('Check', 'Check'), ('Credit Card', 'Credit Card'), ('Trade', 'Trade'), ('Other', 'Other')], max_length=100, blank=True, null=True)
    #workorder = models.ForeignKey(Workorder, blank=False, null=False, on_delete=models.DO_NOTHING)

    def __str__(self):
        #Pulling from Foreign Key
        return self.vendor.name
    
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
    workorder = models.ForeignKey(Workorder, blank=True, null=True, on_delete=models.DO_NOTHING)
    payment_type = models.ForeignKey(PaymentType, blank=False, null=False, on_delete=models.DO_NOTHING)
    check_number = models.CharField('Check Number', max_length=100, blank=True, null=True)
    giftcard_number = models.CharField('GiftCard Number', max_length=100, blank=True, null=True)
    refunded_invoice_number = models.CharField('Refund Invoice Number', max_length=100, blank=True, null=True)
    amount = models.DecimalField('Amount', max_digits=10, decimal_places=2, blank=True, null=True)
    memo = models.CharField('Memo', max_length=500, blank=True, null=True)


    def __str__(self):
        return self.customer.company_name
    
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