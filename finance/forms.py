from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import Payments, AccountsPayable, DailySales, Appliedother
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payments
        fields = ['date', 'customer', 'payment_type', 'amount', 'memo']

class AccountsPayableForm(forms.ModelForm):

    required_css_class = 'required-field'
    #name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Vendor name"}))
    #active = forms.BooleanField(widget=forms.CheckboxInput(attrs={"default": "True"}))
    class Meta:
        model = AccountsPayable
        fields = ['invoice_date', 'vendor', 'description', 'invoice_number', 'amount', 'date_due', 'discount', 'discount_date_due', 'paid', 'date_paid', 'amount_paid']

class DailySalesForm(forms.ModelForm):

    required_css_class = 'required-field'
    #name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Vendor name"}))
    #active = forms.BooleanField(widget=forms.CheckboxInput(attrs={"default": "True"}))
    class Meta:
        model = DailySales
        fields = ['date', 'cash', 'checks', 'creditcard', 'creditcard_fee', 'total']

class AppliedElsewhereForm(forms.ModelForm):

    class Meta:
        model = Appliedother
        fields = ['date', 'customer', 'amount', 'memo']