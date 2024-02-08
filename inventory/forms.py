from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import OrderOut
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class OrderOutForm(forms.ModelForm):
   class Meta:
       model = OrderOut
       fields = ['internal_company', 'description', 'quantity', 'vendor', 'purchase_price', 'unit_price', 'percent_markup','total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Item sell price',

        }