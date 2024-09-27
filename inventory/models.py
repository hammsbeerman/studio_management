from django.db import models
from django.urls import reverse
from django.shortcuts import get_object_or_404
from datetime import datetime
from customers.models import Customer
from workorders.models import Workorder
from controls.models import SubCategory, Measurement, InventoryCategory, GroupCategory
from decimal import Decimal

from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    #post_delete
)
    

    
class Vendor(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=True)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
    city = models.CharField('City', max_length=100, blank=True, null=True)
    state = models.CharField('State', max_length=100, null=True)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=True)
    phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=True)
    phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=True)
    email = models.EmailField('Email', max_length=100, blank=True, null=True)
    website = models.URLField('Website', max_length=100, blank=True, null=True)
    supplier = models.BooleanField('Supplier', blank=False, null=False, default=True)
    retail_vendor = models.BooleanField('Retail Vendor', blank=False, null=False, default=True)
    inventory_vendor = models.BooleanField('Inventory Vendor', blank=False, null=False, default=True)
    non_inventory_vendor = models.BooleanField('Non Inventory Vendor', blank=False, null=False, default=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    #inventorydetails = models.ManyToManyField(Inventory, through="InventoryDetail")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)

    def get_absolute_url(self):
        return reverse("inventory:vendor_detail", kwargs={"id": self.id})

    # def get_hx_url(self):
    #     return reverse("vendors:hx-detail", kwargs={"id": self.id})

    # def get_edit_url(self): #reference these, that way changes are only made one place
    #     return reverse("vendors:update", kwargs={"id": self.id})
    
    # def get_contacts_children(self):
    #     return self.vendorcontact_set.all()
    
class ItemPricingGroup(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("controls:view_price_group_detail", kwargs={"id": self.id})

# class ItemQtyVariations(models.Model):
#     name = models.CharField('Name', max_length=100, blank=False, null=False)
#     measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING)


#     def __str__(self):
#         return self.name
    
class InventoryMaster(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    primary_vendor =  models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    primary_vendor_part_number = models.CharField('Primary Vendor Part Number', max_length=100, blank=True, null=True)
    primary_base_unit = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
    #measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING)
    units_per_base_unit = models.DecimalField('Units per base unit (almost always 1)', max_digits=15, decimal_places=6, blank=True, null=True)
    unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
    price_per_m = models.DecimalField('Price Per M', max_digits=15, decimal_places=4, blank=True, null=True)
    #pricing_group = models.ManyToManyField(GroupCategory, through='InventoryPricingGroup')
    # qty_variations = models.ManyToManyField(ItemQtyVariations, through='InventoryQtyVariations')
    #price_per_sqft = models.DecimalField('Price Per SqFt', max_digits=15, decimal_places=4, blank=True, null=True)
    supplies = models.BooleanField('Supply Item', blank=False, null=False, default=True)
    retail = models.BooleanField('Retail Item', blank=False, null=False, default=True)
    non_inventory = models.BooleanField('Non Inventory Item', blank=False, null=False)
    not_grouped = models.BooleanField('Not Price Grouped', blank=False, null=False, default=False)
    grouped = models.BooleanField('In price group', blank=False, null=False, default=False)
    price_group = models.ManyToManyField(GroupCategory, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    high_price = models.DecimalField('High Price', max_digits=15, decimal_places=6, blank=True, null=True)


    def __str__(self):
        return self.name 
    
    
class InventoryPricingGroup(models.Model):
    inventory = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupCategory, on_delete=models.CASCADE)
    high_price = models.DecimalField('High Price', max_digits=15, decimal_places=4, blank=True, null=True)

    def __str__(self):
        return self.group.name
    
    def get_absolute_url(self):
        return reverse("controls:view_price_group_detail", kwargs={"id": self.group.id})

class InventoryQtyVariations(models.Model):
    inventory = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    # variation = models.ForeignKey(ItemQtyVariations, on_delete=models.CASCADE)
    variation = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
    variation_qty = models.DecimalField('Variation Qty', max_digits=15, decimal_places=4, blank=False, null=False)

    def __str__(self):
        variation_qty = str(self.variation_qty)
        return self.inventory.name + ' -- ' +self.variation.name + ' -- ' + variation_qty 
    
    def get_absolute_url(self):
        return reverse("inventory:item_variation_details", kwargs={"id": self.inventory.id})
    

    
     
    
@receiver(post_save, sender=InventoryMaster)  
def Unit_Cost_Handler(sender, instance, created, *args, **kwargs):
    #print(args, kwargs)
    #print(instance.pk)
    if instance.high_price:
        if instance.units_per_base_unit:
            unit_cost = Decimal(instance.high_price) / instance.units_per_base_unit
            print(unit_cost)
            m = unit_cost * 1000
            unit_cost = round(unit_cost, 6)
            m = round(m, 6)
            InventoryMaster.objects.filter(pk=instance.pk).update(unit_cost=unit_cost, price_per_m=m, updated=datetime.now())
            Inventory.objects.filter(internal_part_number=instance.pk).update(unit_cost=unit_cost, price_per_m=m, updated=datetime.now())
    


# class InventoryDetail(models.Model):
#     invoice_date = models.DateField('Invoice Date', blank=True, null=True)
#     item = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL)
#     vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
#     vendor_item_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
#     invoice_number = models.CharField('Invoice Number', max_length=100, blank=True, null=True)
#     shipped_uom = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='shipped_uom')
#     shipped_qty = models.CharField('Qty', max_length=100, blank=True, null=True)
#     internal_uom = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='internal_uom')
#     internal_qty = models.CharField('Qty', max_length=100, blank=True, null=True)
#     price_per_m = models.CharField('Paper Stock Price per M', max_length=100, blank=True, null=True)
#     total_price = models.CharField('Total Price', max_length=100, blank=True, null=True)
#     #test = models.CharField('test', max_length=100, blank=True)
    
    # def __str__(self):
    #     return self.item

class Inventory(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(InventoryMaster, blank=True, null=True, on_delete=models.CASCADE)
    unit_cost = models.CharField('Unit Cost', max_length=100, blank=True, null=True)
    price_per_m = models.CharField('Paper Stock Price per M', max_length=100, blank=True, null=True)
    price_per_sqft = models.CharField('Price per SqFt', max_length=100, blank=True, null=True)
    current_stock = models.CharField('Current Stock', max_length=100, blank=True, null=True)
    #vendor = models.ManyToManyField(Vendor)
    # vendor_part_number
    color = models.CharField('Color', max_length=100, blank=True, null=True)
    size = models.CharField('Size', max_length=100, blank=True, null=True)
    width = models.CharField('Width', max_length=100, blank=True, null=True)
    width_measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='width_mea')
    length = models.CharField('Length', max_length=100, blank=True, null=True)
    length_measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='length_mea')
    measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING)
    type_paper = models.BooleanField('Paper', default=False)
    type_envelope = models.BooleanField('Envelope', default=False)
    type_wideformat = models.BooleanField('Wide Format', default=False)
    type_vinyl = models.BooleanField('Vinyl', default=False)
    type_mask = models.BooleanField('Mask', default=False)
    type_laminate = models.BooleanField('Laminate', default=False)
    type_substrate = models.BooleanField('Substrate', default=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    inventory_category = models.ManyToManyField(InventoryCategory)
    retail_item = models.BooleanField('Retail Item', default=True)
    #retail_category = 

    def __str__(self):
        return self.name

class VendorItemDetail(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    #internal_part_number = models.CharField('Internal Part Number', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    supplies = models.BooleanField('Supply Item', blank=False, null=False)
    retail = models.BooleanField('Retail Item', blank=False, null=False)
    non_inventory = models.BooleanField('Non Inventory Item', blank=False, null=False)
    #internal_part_number = models.ManyToManyField(RetailInventoryMaster)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    high_price = models.DecimalField('High Price', max_digits=15, decimal_places=4, blank=True, null=True)

    def __str__(self):
        return self.name
    
    

class OrderOut(models.Model):
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')], max_length=100, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    vendor = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.DO_NOTHING)
    purchase_price = models.DecimalField('Purchase Price', max_digits=8, decimal_places=2, blank=True, null=True)
    percent_markup = models.DecimalField('Percent Markup', max_digits=8, decimal_places=2, blank=True, null=True)
    quantity = models.DecimalField('Quantity', max_digits=8, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    dateentered = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    billed = models.BooleanField('Billed', blank=False, null=False, default=False)
    edited = models.BooleanField('Edited', blank=False, null=False, default=False)

    def __str__(self):
        return self.workorder.workorder
    
class SetPrice(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')], max_length=100, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    setprice_category = models.CharField('Item Category', max_length=10, blank=True, null=True)
    setprice_item = models.CharField('Item', max_length=10, blank=True, null=True)
    setprice_qty = models.CharField('Pieces / set', max_length=10, blank=True, null=True)
    setprice_price = models.CharField('Price / set', max_length=10, blank=True, null=True)
    total_pieces = models.CharField('Total pieces', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    paper_stock = models.ForeignKey(Inventory, blank=True, null=True, on_delete=models.SET_NULL)
    side_1_inktype = models.CharField('Side 1 Ink', choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')], max_length=100, blank=True, null=True)
    side_2_inktype = models.CharField('Side 2 Ink', choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')], max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField('Quantity', blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    dateentered = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    billed = models.BooleanField('Billed', blank=False, null=False, default=False)
    edited = models.BooleanField('Edited', blank=False, null=False, default=False)

    def __str__(self):
        return self.workorder.workorder

class Photography(models.Model):
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')], max_length=100, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    subcategory = models.CharField('Subcategory', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    quantity = models.DecimalField('Quantity', max_digits=6, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    dateentered = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    billed = models.BooleanField('Billed', blank=False, null=False, default=False)
    edited = models.BooleanField('Edited', blank=False, null=False, default=False)





#Add item to inventory if added to inventorymaster
@receiver(post_save, sender=InventoryMaster)  
def Inventory_Master_Handler(sender, instance, created, *args, **kwargs):
    #print(args, kwargs)
    try:
        obj = get_object_or_404(Inventory, internal_part_number=instance.pk)
        #print(obj)
        print('found')
    except:
        print('not found')
        name = instance.name
        description = instance.description
        unit_cost = instance.unit_cost
        m = instance.price_per_m
        measurement = instance.primary_base_unit
        retail = instance.retail
        if not unit_cost:
            unit_cost=0
        item = Inventory(name=name, description=description, internal_part_number=InventoryMaster.objects.get(pk=instance.pk), unit_cost=unit_cost, price_per_m=m , measurement=measurement, retail_item=retail, created=datetime.now(), updated=datetime.now())
        item.save()


        


###################Not used yet

class VendorContact(models.Model):
    vendor = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.SET_NULL)
    #company = models.OneToOneField(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    fname = models.CharField('First Name', max_length=100, blank=True, null=True)
    lname = models.CharField('Last Name', max_length=100, blank=True, null=True)
    phone1 = models.CharField('Phone', max_length=100, blank=True, null=True)
    email = models.EmailField('Email', max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)














# #Create master inventory item from items already in inventory list
# def create_inventory_from_inventory(request):
#     inventory = Inventory.objects.all()[:120]
#     print(inventory)
#     for x in inventory:
#         if not x.internal_part_number:
#             name = x.name
#             description = x.description
#             p_vpn = x.vendor_part_number
#             measurement = x.measurement
#             unit_cost = x.unit_cost
#             m = x.price_per_m
#             if not unit_cost:
#                 unit_cost=0
#             item = InventoryMaster(name=name, description=description, supplies=1, retail=1, primary_vendor_part_number=p_vpn, primary_base_unit=measurement, unit_cost=unit_cost, price_per_m=m)
#             item.save()
#             print('saved')
#             print(item.pk)
#             ipn = Inventory.objects.filter(pk=x.pk).update(internal_part_number=item.pk)
#             print('IPN')
#             print(ipn)
#             #Inventory.objects.filter(internal_part_number=instance.pk).update(unit_cost=unit_cost, price_per_m=m, updated=datetime.now())
#     return render (request, "controls/specialized_tools.html")


    
