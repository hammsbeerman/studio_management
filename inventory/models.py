from django.db import models
from django.urls import reverse
from customers.models import Customer
from workorders.models import Workorder
from controls.models import SubCategory, Measurement, InventoryCategory




class Inventory(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    internal_part_number = models.CharField('Internal Part Number', max_length=100, blank=True, null=True)
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

    

    def __str__(self):
        return self.name
    
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
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    inventorydetails = models.ManyToManyField(Inventory, through="InventoryDetail")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("inventory:detail", kwargs={"id": self.id})

    # def get_hx_url(self):
    #     return reverse("vendors:hx-detail", kwargs={"id": self.id})

    # def get_edit_url(self): #reference these, that way changes are only made one place
    #     return reverse("vendors:update", kwargs={"id": self.id})
    
    # def get_contacts_children(self):
    #     return self.vendorcontact_set.all()
    

class InventoryDetail(models.Model):
    item = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL)
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    vendor_item_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    test = models.CharField('test', max_length=100, blank=True)

    # def __str__(self):
    #     return self.item





class OrderOut(models.Model):
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.SET_NULL)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, blank=False, null=False)
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    vendor = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.DO_NOTHING)
    purchase_price = models.DecimalField('Purchase Price', max_digits=6, decimal_places=2, blank=True, null=True)
    percent_markup = models.DecimalField('Percent Markup', max_digits=6, decimal_places=2, blank=True, null=True)
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

    def __str__(self):
        return self.workorder.workorder
    
class SetPrice(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.SET_NULL)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, blank=False, null=False)
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
    side_2_inktype = models.CharField('Side 1 Ink', choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')], max_length=100, blank=True, null=True)
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
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.SET_NULL)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, blank=False, null=False)
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


    
