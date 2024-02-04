from django.db import models
from django.conf import settings
from django.urls import reverse
#from inventory.utils import number_str_to_float
#from inventory.validators import validate_unit_of_measure

# Create your models here.
"""
Vendor
    - Name
    - Address
    - Phone
    - Contact
    - Website

Vendor Contact

"""

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