from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import SubCategory, Category, SetPriceCategory, SetPriceItemPrice
from inventory.models import InventoryPricingGroup, Inventory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class SubCategoryForm(forms.ModelForm):

    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'description', 'inventory_category']

class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description', 'design_type', 'formname', 'modal']

class AddSetPriceCategoryForm(forms.ModelForm):
   class Meta:
       model = SetPriceCategory
       fields = ['name', 'category', 'updated']
       labels = {
            
        }
       
class AddSetPriceItemForm(forms.ModelForm):
   class Meta:
       model = SetPriceItemPrice
       fields = ['name', 'description', 'set_quantity', 'price', 'updated']
       labels = {
            'name':'Group',

        }
       
class AddInventoryPricingGroupForm(forms.ModelForm):
    class Meta:
        model = InventoryPricingGroup
        fields = ['inventory', 'group']

class AddItemtoListForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['type_paper', 'type_envelope', 'type_wideformat', 'type_vinyl', 'type_mask', 'type_laminate', 'type_substrate', 'inventory_category', 'retail_item']
        widgets = {
            'inventory_category': forms.CheckboxSelectMultiple(),  # or forms.SelectMultiple()
        }