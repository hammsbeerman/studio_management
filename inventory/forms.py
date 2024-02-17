from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import OrderOut, SetPrice, Photography, Vendor
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from localflavor.us.forms import USStateSelect

class AddVendorForm(forms.ModelForm):
   state = forms.CharField(widget=USStateSelect(), initial='WI')
   class Meta:
       model = Vendor
       fields = ['name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'website']
       labels = {
        }

class OrderOutForm(forms.ModelForm):
   class Meta:
       model = OrderOut
       fields = ['internal_company', 'description', 'quantity', 'vendor', 'purchase_price', 'percent_markup','total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Calculated Item sell price',

        }
       
class SetPriceForm(forms.ModelForm):
   class Meta:
       model = SetPrice
       fields = ['internal_company', 'description', 'quantity', 'setprice_category', 'setprice_item', 'setprice_qty', 'paper_stock', 'side_1_inktype', 'side_2_inktype', 'setprice_price', 'unit_price', 'total_pieces', 'total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Item sell price',

        }
       
class PhotographyForm(forms.ModelForm):
   class Meta:
       model = Photography
       fields = ['internal_company', 'description', 'quantity', 'unit_price', 'total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Item sell price',

        }
       


       
    