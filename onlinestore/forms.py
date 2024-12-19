from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import StoreItemDetails
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class StoreItemDetailForm(forms.ModelForm):

    class Meta:
        model = StoreItemDetails
        fields = ['item', 'online_store_price', 'retail_store_price']

        