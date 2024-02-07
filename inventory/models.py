from django.db import models
from django.urls import reverse
from workorders.models import Category

class Inventory(models.Model):
    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100, blank=False, null=True)
    name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    internal_part_number = models.CharField('Internal Part Number', max_length=100, blank=True, null=True)
    unit_cost = models.CharField('Unit Cost', max_length=100, blank=True, null=True)
    current_stock = models.CharField('Current Stock', max_length=100, blank=True, null=True)
    #vendor = models.ManyToManyField(Vendor)
    # vendor_part_number
    color = models.CharField('Color', max_length=100, blank=True, null=True)
    size = models.CharField('Size', max_length=100, blank=True, null=True)
    measurement = models.CharField('Measurement', max_length=100, blank=True, null=True)
    type_paper = models.BooleanField(default=False)
    type_envelope = models.BooleanField(default=False)
    type_wideformat = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    

    def __str__(self):
        return self.name
    
class Vendor(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=True)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
    city = models.CharField('City', max_length=100, null=True)
    state = models.CharField('State', max_length=100, null=True)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=True)
    phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=True)
    phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=True)
    email = models.EmailField('Email', max_length=100, blank=True, null=True)
    website = models.URLField('Website', max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    inventorydetail = models.ManyToManyField(Inventory, through="InventoryDetails")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("vendors:detail", kwargs={"id": self.id})

    def get_hx_url(self):
        return reverse("vendors:hx-detail", kwargs={"id": self.id})

    def get_edit_url(self): #reference these, that way changes are only made one place
        return reverse("vendors:update", kwargs={"id": self.id})
    
    def get_contacts_children(self):
        return self.vendorcontact_set.all()
    

class InventoryDetails(models.Model):
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    vendor_item_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)


###################Not used yet

class VendorContact(models.Model):
    vendor = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.CASCADE)
    #company = models.OneToOneField(Customer, on_delete=models.CASCADE, blank=True, null=True)
    fname = models.CharField('First Name', max_length=100, blank=True, null=True)
    lname = models.CharField('Last Name', max_length=100, blank=True, null=True)
    phone1 = models.CharField('Phone', max_length=100, blank=True, null=True)
    email = models.EmailField('Email', max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    
