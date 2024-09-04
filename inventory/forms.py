from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.db.models.functions import Lower
from .models import OrderOut, SetPrice, Photography, Vendor, InventoryMaster, VendorItemDetail
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from localflavor.us.forms import USStateSelect

class AddVendorForm(forms.ModelForm):
   state = forms.CharField(widget=USStateSelect(), initial='WI')
   class Meta:
       model = Vendor
       fields = ['name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'website', 'supplier', 'retail_vendor']
       labels = {
        }
       
class InventoryMasterForm(forms.ModelForm):
    class Meta:
        model = InventoryMaster
        fields = ['name', 'description', 'primary_vendor', 'primary_vendor_part_number', 'primary_base_unit', 'units_per_base_unit', 'supplies', 'retail', 'non_inventory']
        labels = {
        } 

class VendorItemDetailForm(forms.ModelForm):
    class Meta:
        model = VendorItemDetail
        fields = ['name', 'vendor_part_number', 'description', 'internal_part_number']
        labels = {
        } 

class OrderOutForm(forms.ModelForm):
   vendor = forms.ModelChoiceField(queryset=Vendor.objects.all().order_by(Lower('name')))

   class Meta:
       model = OrderOut
       fields = ['internal_company', 'description', 'quantity', 'vendor', 'purchase_price', 'percent_markup','total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Calculated Item sell price',

        }
       widgets = {
       'last_item_order': forms.TextInput(attrs={'readonly':'readonly'}),
       'last_item_price': forms.TextInput(attrs={'readonly':'readonly'}),
       }
       
class SetPriceForm(forms.ModelForm):
   class Meta:
       model = SetPrice
       fields = ['internal_company', 'description', 'quantity', 'setprice_category', 'setprice_item', 'setprice_qty', 'paper_stock', 'side_1_inktype', 'side_2_inktype', 'setprice_price', 'unit_price', 'total_pieces', 'total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Item sell price',

        }
       widgets = {
       'last_item_order': forms.TextInput(attrs={'readonly':'readonly'}),
       'last_item_price': forms.TextInput(attrs={'readonly':'readonly'}),
       }
       
class PhotographyForm(forms.ModelForm):
   class Meta:
       model = Photography
       fields = ['internal_company', 'description', 'quantity', 'unit_price', 'total_price', 'override_price', 'last_item_order', 'last_item_price']
       labels = {
            'total_price':'Item sell price',

        }
       widgets = {
       'last_item_order': forms.TextInput(attrs={'readonly':'readonly'}),
       'last_item_price': forms.TextInput(attrs={'readonly':'readonly'}),
       }
       
# class AddInventoryItemForm(forms.ModelForm):
#    #state = forms.CharField(widget=USStateSelect(), initial='WI')
#    class Meta:
#        model = InventoryDetail
#        fields = ['invoice_date', 'item', 'vendor', 'vendor_item_number', 'invoice_number', 'shipped_uom', 'shipped_qty', 'internal_uom', 'internal_qty', 'price_per_m', 'total_price']
#        labels = {
#         }
       


       
    