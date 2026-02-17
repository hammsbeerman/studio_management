import calendar
from datetime import date
from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import Payments, AccountsPayable, DailySales, Appliedother, InvoiceItem
from customers.models import Customer
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
        fields = ['invoice_date', 'vendor', 'description', 'invoice_number', 'amount', 'date_due', 'discount', 'discount_date_due', 'paid', 'date_paid', 'amount_paid', 'payment_method', 'check_number', 'posted']


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

# class WorkorderPayment(forms.ModelForm):
#    #state = forms.CharField(widget=USStateSelect(), initial='WI')
#    class Meta:
#        model = WorkorderPayment
#        fields = ['workorder', 'payment', 'payment_amount', 'date']
#        labels = {
#         }

class AddInvoiceForm(forms.ModelForm):
   class Meta:
       model = AccountsPayable
       fields = ['invoice_date', 'invoice_number', 'description', 'total', 'date_due', 'discount', 'discount_date_due', 'paid', 'date_paid', 'amount_paid', 'payment_method', 'check_number']
       labels = {
        }
       
class EditInvoiceForm(forms.ModelForm):
   class Meta:
       model = AccountsPayable
       fields = ['invoice_date', 'invoice_number', 'description', 'vendor', 'total', 'date_due', 'discount', 'discount_date_due', 'paid', 'date_paid', 'amount_paid', 'payment_method', 'check_number', 'posted', 'void', 'void_reason']
       labels = {
        }
       
class BulkEditInvoiceForm(forms.ModelForm):
   class Meta:
       model = AccountsPayable
       fields = ['date_paid', 'payment_method', 'check_number']
       labels = {
        }
       
class AddInvoiceItemForm(forms.ModelForm):
   class Meta:
       model = InvoiceItem
       fields = ['name', 'vendor_part_number', 'description', 'internal_part_number', 'vendor', 'invoice_unit_cost', 'invoice_qty']
       labels = {
        }
       
       
class AddInvoiceItemRemainderForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['vendor_part_number', 'description', 'invoice_unit_cost', 'invoice_qty']
        labels = {
        } 

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}))
    end_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}))

class SalesComparisonForm(forms.Form):
    period1_start = forms.DateField(
        label="Period 1 start",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    period1_end = forms.DateField(
        label="Period 1 end",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    period2_start = forms.DateField(
        label="Period 2 start",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    period2_end = forms.DateField(
        label="Period 2 end",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.order_by("company_name"),
        required=False,
        label="Customer (optional)",
        widget=forms.Select(attrs={"class": "form-select select2"}),
    )

    COMPANY_CHOICES = [
        ("Krueger Printing", "Krueger Printing"),
        ("LK Design", "LK Design"),
        ("Office Supplies", "Office Supplies"),
    ]
    companies = forms.MultipleChoiceField(
        label="Companies",
        required=False,
        choices=COMPANY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    combine_companies = forms.BooleanField(
        label="Combine selected companies into one row per customer",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            today = date.today()

            # last month relative to today
            if today.month > 1:
                last_month = today.month - 1
                last_month_year = today.year
            else:
                last_month = 12
                last_month_year = today.year - 1

            # Last day of that last_month
            _, last_month_days = calendar.monthrange(last_month_year, last_month)
            last_month_end_this_year = date(last_month_year, last_month, last_month_days)

            # Period 2: Jan 1 of last_month_year → end of that last month
            period2_start = date(last_month_year, 1, 1)
            period2_end = last_month_end_this_year

            # Period 1: previous year, same structure
            year1 = last_month_year - 1
            _, last_month_days1 = calendar.monthrange(year1, last_month)
            period1_start = date(year1, 1, 1)
            period1_end = date(year1, last_month, last_month_days1)

            self.initial["period1_start"] = period1_start
            self.initial["period1_end"] = period1_end
            self.initial["period2_start"] = period2_start
            self.initial["period2_end"] = period2_end

        self.fields["customer"].empty_label = "All customers"