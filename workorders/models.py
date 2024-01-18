from django.db import models
from django.urls import reverse
from customers.models import Customer, Contact

class Workorder(models.Model):
    customer = models.ForeignKey(Customer, blank=False, null=False, on_delete=models.CASCADE, related_name='workorders')
    contact = models.ForeignKey(Contact, blank=True, null=True, on_delete=models.SET_NULL)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True,)
    hr_contact = models.CharField('Contact Name', max_length=100, blank=True, null=True,)
    ##company = models.OneToOneField(Customer, on_delete=models.CASCADE, blank=True, null=True)
    workorder = models.CharField('Workorder', max_length=100, blank=False, null=False, unique=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, blank=False, null=False)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    deadline = models.DateField('Deadline', blank=True, null=True)
    po_number = models.CharField('PO Number', max_length=100, blank=True, null=True)
    budget = models.CharField('Budget', max_length=100, blank=True, null=True)
    quoted_price = models.CharField('Quoted Price', max_length=100, blank=True, null=True)
    original_order = models.CharField('Original Order', max_length=100, blank=True, null=True)
    lk_workorder = models.CharField('LK Workorder', max_length=100, blank=True, null=True)
    printleader_workorder = models.CharField('Printleader', max_length=100, blank=True, null=True)

    def get_absolute_url(self):
        return reverse("workorders:items", kwargs={"id": self.workorder})
    
    def get_item_url(self):
        return reverse("workorders:items", kwargs={"id": self.workorder})
    
class Numbering(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False, unique=True)
    value = models.PositiveIntegerField('Value', blank=False, null=False)

    def __str__(self):
        return self.name
    

    #@property
    #def WorkorderNum(self):
    #    return self.workorder
    
    