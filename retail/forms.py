from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.db.models.functions import Lower
from finance.models import AccountsPayable, InvoiceItem
from inventory.models import Vendor, InventoryMaster
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from localflavor.us.forms import USStateSelect


class AddVendorForm(forms.ModelForm):
   state = forms.CharField(widget=USStateSelect(), initial='WI')
   class Meta:
       model = Vendor
       fields = ['name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'website', 'supplier']
       labels = {
        }
       
# class AddInvoiceForm(forms.ModelForm):
#    class Meta:
#        model = AccountsPayable
#        fields = ['invoice_date', 'invoice_number', 'vendor', 'total', 'date_due', 'discount', 'discount_date_due', 'paid', 'date_paid', 'amount_paid', 'payment_method', 'retail_invoice', 'supplies_invoice']
#        labels = {
#         }
       
# class AddInvoiceItemForm(forms.ModelForm):
#    class Meta:
#        model = InvoiceItem
#        fields = ['name', 'vendor_part_number', 'description', 'internal_part_number', 'vendor', 'unit_cost', 'qty']
#        labels = {
#         }
       
       
# class AddInvoiceItemRemainderForm(forms.ModelForm):
#     class Meta:
#         model = InvoiceItem
#         fields = ['vendor_part_number', 'description', 'unit_cost', 'qty']
#         labels = {
#         } 

# class VendorItemRemainderForm(forms.ModelForm):
#     class Meta:
#         model = RetailVendorItemDetail
#         fields = ['vendor_part_number', 'description', 'unit_cost', 'qty']
#         labels = {
#         } 

# class RetailVendorItemDetailForm(forms.ModelForm):
#     class Meta:
#         model = RetailVendorItemDetail
#         fields = ['name', 'vendor_part_number', 'description', 'internal_part_number']
#         labels = {
#         } 

class RetailInventoryMasterForm(forms.ModelForm):
    class Meta:
        model = InventoryMaster
        fields = ['name', 'description', 'primary_vendor', 'primary_vendor_part_number']
        labels = {
        } 


        







       