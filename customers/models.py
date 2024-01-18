from django.db import models

from django.urls import reverse

class Customer(models.Model):
    company_name = models.CharField('Company Name', max_length=100, blank=True, null=False)
    first_name = models.CharField('First Name', max_length=100, blank=True, null=False)
    last_name = models.CharField('Last Name', max_length=100, blank=True, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=False)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=False)
    city = models.CharField('City', max_length=100, blank=True, null=False)
    state = models.CharField('State', max_length=100, blank = True, null=False)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=False)
    phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=False)
    phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=False)
    email = models.EmailField('Email', max_length=100, blank=True, null=False)
    website = models.URLField('Website', max_length=100, blank=True, null=False)
    po_number = models.CharField('PO Number', max_length=100, blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("customers:detail", kwargs={"id": self.id})

    def __str__(self):
        return self.company_name

    #def __str__(self):
    #    return self.id
    

    
class Contact(models.Model):
    customer = models.ForeignKey(Customer, blank=False, null=False, on_delete=models.CASCADE, related_name='contacts')
    #company = models.OneToOneField(Customer, on_delete=models.CASCADE, blank=True, null=True)
    fname = models.CharField('First Name', max_length=100, blank=True, null=False)
    lname = models.CharField('Last Name', max_length=100, blank=True, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=False)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=False)
    city = models.CharField('City', max_length=100, blank=True, null=False)
    state = models.CharField('State', max_length=100, blank = True, null=False)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=False)
    phone1 = models.CharField('Phone', max_length=100, blank=True, null=False)
    email = models.EmailField('Email', max_length=100, blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)

    def get_absolute_url(self):
        return self.customer.get_absolute_url()
    
    # def get_hx_edit_url(self):
    #     kwargs = {
    #         "parent_id": self.customer.id,
    #         "id": self.id
    #     }
    #     return reverse("customers:hx-contact-update", kwargs=kwargs)

    def __str__(self):
        return self.fname