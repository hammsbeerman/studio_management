from django.db import models

from django.urls import reverse

class Customer(models.Model):

    Tax_Exempt = (
    (True, 'Yes'),
    (False, 'No')
)
    

    company_name = models.CharField('Company Name', max_length=100, blank=True, null=False)
    first_name = models.CharField('First Name', max_length=100, blank=True, null=False)
    last_name = models.CharField('Last Name', max_length=100, blank=True, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=False)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
    city = models.CharField('City', max_length=100, blank=True, null=False)
    state = models.CharField('State', max_length=100, blank = True, null=False)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=False)
    phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=False)
    phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=False)
    email = models.EmailField('Email', max_length=100, blank=True, null=False)
    website = models.URLField('Website', max_length=100, blank=True, null=False)
    logo = models.ImageField('Logo', blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    po_number = models.CharField('PO Number', max_length=100, blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    last_workorder = models.DateTimeField(auto_now = False, blank=True, null=True)
    active = models.BooleanField(default=True)
    customer_number = models.CharField('Customer Number', max_length=100, blank=True, null=False)
    tax_exempt = models.BooleanField('Tax Exempt', default=False, choices=Tax_Exempt)
    tax_exempt_number = models.CharField('Tax ID Number', max_length=100, blank=True, null=True)
    tax_exempt_paperwork = models.ImageField(upload_to="tax_exempt_form/", blank=True, null=True)
    credit = models.DecimalField('Credits', max_digits=8, decimal_places=2, blank=True, null=True)
    open_balance = models.DecimalField('Open Balance', max_digits=8, decimal_places=2, blank=True, null=True)
    high_balance = models.DecimalField('High Balance', max_digits=8, decimal_places=2, blank=True, null=True)
    avg_days_to_pay = models.CharField('Avg Days to Pay', max_length=100, blank=True, null=False)
    
    def get_absolute_url(self):
        return reverse("customers:expanded_details", kwargs={"id": self.id})

    def __str__(self):
        return self.company_name

    #def __str__(self):
    #    return self.id
    

    
class Contact(models.Model):
    customer = models.ForeignKey(Customer, blank=False, null=True, on_delete=models.SET_NULL, related_name='contacts')
    #company = models.OneToOneField(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    fname = models.CharField('First Name', max_length=100, blank=False, null=False)
    lname = models.CharField('Last Name', max_length=100, blank=True, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=False)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
    city = models.CharField('City', max_length=100, blank=True, null=False)
    state = models.CharField('State', max_length=100, blank = True, null=False)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=False)
    phone1 = models.CharField('Phone', max_length=100, blank=True, null=False)
    email = models.EmailField('Email', max_length=100, blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)

    def get_absolute_url(self):
        return self.customer.get_absolute_url()
    
    # def edit_print_item_url(self):
    #     #return reverse("krueger:bigform", kwargs={"id": self.workorder})
    #     return reverse("krueger:bigform", kwargs={"id": self.workorder, "pk":self.pk})
    
    # def get_hx_edit_url(self):
    #     kwargs = {
    #         "parent_id": self.customer.id,
    #         "id": self.id
    #     }
    #     return reverse("customers:hx-contact-update", kwargs=kwargs)

    def __str__(self):
        return self.fname
    

class ShipTo(models.Model):
    customer = models.ForeignKey(Customer, blank=False, null=True, on_delete=models.SET_NULL, related_name='shipto')
    company_name = models.CharField('Company Name', max_length=100, blank=True, null=False)
    first_name = models.CharField('First Name', max_length=100, blank=True, null=False)
    last_name = models.CharField('Last Name', max_length=100, blank=True, null=False)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=False)
    address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
    city = models.CharField('City', max_length=100, blank=True, null=False)
    state = models.CharField('State', max_length=100, blank = True, null=False)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=False)
    phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=False)
    phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=False)
    email = models.EmailField('Email', max_length=100, blank=True, null=False)
    website = models.URLField('Website', max_length=100, blank=True, null=False)
    logo = models.ImageField('Logo', blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    active = models.BooleanField(default=True)
    #company = models.OneToOneField(Customer, on_delete=models.SET_NULL, blank=True, null=True)

    def get_absolute_url(self):
        return self.customer.get_absolute_url()

    def __str__(self):
        return self.company_name



    