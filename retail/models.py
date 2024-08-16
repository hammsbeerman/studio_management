from django.db import models
from django.urls import reverse
from controls.models import RetailInventoryCategory, Measurement
from inventory.models import Inventory, Vendor

# class RetailVendor(models.Model):
#     name = models.CharField('Name', max_length=100, blank=False, null=False)
#     address1 = models.CharField('Address 1', max_length=100, blank=True, null=True)
#     address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
#     city = models.CharField('City', max_length=100, blank=True, null=True)
#     state = models.CharField('State', max_length=100, null=True)
#     zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=True)
#     phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=True)
#     phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=True)
#     email = models.EmailField('Email', max_length=100, blank=True, null=True)
#     website = models.URLField('Website', max_length=100, blank=True, null=True)
#     supplier = models.BooleanField('Supplier', blank=False, null=False, default=True)
#     created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
#     updated = models.DateTimeField(auto_now = True, blank=False, null=False)
#     #inventorydetails = models.ManyToManyField(RetailInventory, through="RetailInventoryDetail")
#     active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name
    
#     def get_absolute_url(self):
#         return reverse("retail:vendor_detail", kwargs={"id": self.id})
    
##!   
class RetailInvoices(models.Model):
    invoice_date = models.DateField('Invoice Date', blank=True, null=True)
    invoice_number = models.CharField('Invoice Number', max_length=100, blank=True, null=False)
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    total = models.CharField('Total', max_length=100, blank=True, null=True)
    date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    discount = models.DecimalField('Discount', blank=True, null=True, max_digits=10, decimal_places=2)
    discount_date_due = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    paid = models.BooleanField('Paid', null=True, default=False)
    date_paid = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    amount_paid = models.DecimalField('Amount Paid', blank=True, null=True, max_digits=10, decimal_places=2)
    payment_method = models.CharField('Payment Method', choices=[('Cash', 'Cash'), ('Check', 'Check'), ('Credit Card', 'Credit Card'), ('Trade', 'Trade'), ('Other', 'Other')], max_length=100, blank=True, null=True)
    

    def __str__(self):
         return self.invoice_number
    
    def get_absolute_url(self):
        return reverse("retail:invoice_detail", kwargs={"id": self.id})


##!
class RetailInventoryMaster(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    primary_vendor =  models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    primary_vendor_part_number = models.CharField('Primary Vendor Part Number', max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    high_price = models.CharField('High Price', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
   
    
class RetailVendorItemDetail(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    #internal_part_number = models.CharField('Internal Part Number', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(RetailInventoryMaster, on_delete=models.CASCADE)
    #internal_part_number = models.ManyToManyField(RetailInventoryMaster)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    high_price = models.DecimalField('High Price', max_digits=8, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.name
    
    
class RetailInvoiceItem(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(RetailInvoices, blank=True, null=True, on_delete=models.DO_NOTHING)
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    #name = models.ForeignKey(RetailInventoryMaster, on_delete=models.CASCADE, related_name='item_name')
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    #internal_part_number = models.CharField('Internal Part Number', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(RetailInventoryMaster, on_delete=models.CASCADE)
    unit_cost = models.DecimalField('Unit Cost', max_digits=8, decimal_places=2, blank=True, null=True)
    qty = models.DecimalField('Qty', max_digits=8, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    #inventory_category = models.ManyToManyField(RetailInventoryCategory)
    #retail_item = models.BooleanField('Retail Item', default=True)    

    def __str__(self):
        return self.name
    
    


# class PriceBreaks(models.Model):
#     name = models.CharField('Name', max_length=100, blank=True, null=True)
#     qty_full_price = models.DecimalField('Full Price Qty', max_digits=10, decimal_places=2, blank=True, null=True)
#     full_price_pct = models.DecimalField('Full Price Pct', max_digits=10, decimal_places=2, blank=True, null=True)
#     qty_break_one = models.DecimalField('Break 1 Qty', max_digits=10, decimal_places=2, blank=True, null=True)
#     break_one_pct = models.DecimalField('Break 1 Pct', max_digits=10, decimal_places=2, blank=True, null=True)
#     qty_break_two = models.DecimalField('Break 2 Qty', max_digits=10, decimal_places=2, blank=True, null=True)
#     break_two_pct = models.DecimalField('Break 2 Pct', max_digits=10, decimal_places=2, blank=True, null=True)

# class OfficeSupplies(models.Model):
#     name = models.CharField('Name', max_length=100, blank=True, null=True)

# class RetailInventory(models.Model):
#     name = models.CharField('Name', max_length=100, blank=False, null=False)
#     name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     internal_part_number = models.CharField('Internal Part Number', max_length=100, blank=True, null=True)
#     unit_cost = models.CharField('Unit Cost', max_length=100, blank=True, null=True)
#     current_stock = models.CharField('Current Stock', max_length=100, blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
#     updated = models.DateTimeField(auto_now = True, blank=False, null=False)
#     inventory_category = models.ManyToManyField(RetailInventoryCategory)
#     retail_item = models.BooleanField('Retail Item', default=True)    

#     def __str__(self):
#         return self.name

# class RetailInventoryDetail(models.Model):
#     paper_item = models.ForeignKey(RetailInventory, blank=True, null=True, on_delete=models.DO_NOTHING)
#     office_supply_item = models.ForeignKey(OfficeSupplies, blank=True, null=True, on_delete=models.DO_NOTHING)
#     name = models.CharField('Name', max_length=100, blank=True, null=True)
#     name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     price = models.DecimalField('Price', max_digits=10, decimal_places=2, blank=True, null=True)
#     qty_on_hand = models.DecimalField('Qty on Hand', max_digits=10, decimal_places=2, blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
#     updated = models.DateTimeField(auto_now = True, blank=False, null=False)
#     inventory_category = models.ManyToManyField(RetailInventoryCategory)
#     # purchase_price = 
#     # sell_price = 
#     # sale_price = 
#     # on_sale = 

#     def __str__(self):
#         return self.item.name




# class RetailPurchaseHistory(models.Model):
#     invoice_date = models.DateField('Invoice Date', blank=True, null=True)
#     item = models.ForeignKey(RetailInventory, null=True, on_delete=models.SET_NULL)
#     vendor = models.ForeignKey(RetailVendor, null=True, on_delete=models.SET_NULL)
#     vendor_item_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
#     invoice_number = models.CharField('Invoice Number', max_length=100, blank=True, null=True)
#     shipped_uom = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='retail_shipped_uom')
#     shipped_qty = models.CharField('Qty', max_length=100, blank=True, null=True)
#     internal_uom = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING)
#     internal_qty = models.CharField('Qty', max_length=100, blank=True, null=True)
#     price_per_m = models.CharField('Paper Stock Price per M', max_length=100, blank=True, null=True)
#     total_price = models.CharField('Total Price', max_length=100, blank=True, null=True)

#     def __str__(self):
#          return self.item






    


    
    




    
    
