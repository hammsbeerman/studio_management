from django import forms
from django.forms import ModelForm
from decimal import Decimal
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

PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("check", "Check"),
    ("card", "Credit/Debit Card"),
    ("gift", "Gift Certificate"),
    ("other", "Other"),
]

class PaymentMethodForm(forms.Form):
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    amount = forms.DecimalField(
        max_digits=9,
        decimal_places=2,
        required=False,  # let the view fall back if empty
        label="Amount",
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Notes",
    )
    check_number = forms.CharField(
        max_length=64,
        required=False,
        label="Check number",
        help_text="Only used for check payments.",
    )

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("payment_method")
        check_number = cleaned.get("check_number")

        # If you want to *require* a check number whenever method is check,
        # make sure the value "check" matches your actual choice key.
        if method == "check" and not check_number:
            self.add_error("check_number", "Please enter the check number.")
        return cleaned

class RefundLookupForm(forms.Form):
    invoice_number = forms.CharField(
        label="POS Invoice #",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

        







       