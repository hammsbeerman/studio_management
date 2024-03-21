from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import Payments
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payments
        fields = ['date', 'customer', 'payment_type', 'amount', 'memo']
