from django.utils.safestring import mark_safe
from django import forms
from .models import Workorder, WorkorderItem
from controls.models import Numbering
from customers.models import Customer, Contact
from dynamic_forms import DynamicField, DynamicFormMixin
from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class WorkorderForm(DynamicFormMixin, forms.ModelForm):
    #required_css_class = 'required-field'
    #description = forms.CharField(label="Description", widget=forms.Textarea())
    class Meta:
        model = Workorder
        fields = ['internal_company', 'quote', 'description', 'deadline', 'po_number', 'budget', 'quoted_price', 'original_order', 'lk_workorder', 'printleader_workorder']
        labels = {
            'workorder':'Workorder',
            'deadline':'Deadline',
            'internal_company': 'Pick company'
            }
        widgets = {
            'workorder': forms.TextInput(attrs={'class':'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        for field in self.fields:
            #print(field)
            new_data = {
                "placeholder": f'{str(field)}',
                "class": 'form-control',
                #"hx-post": ".",
                #"hx-trigger": "keyup changed delay:500ms",
                #"hx-target": "#recipe-container",
                #"hx-swap": "innerHTML"
            }
            self.fields[str(field)].widget.attrs.update(new_data)
        self.fields['internal_company'].widget.attrs.update({'initial': 'Select Company'})
        self.fields['description'].widget.attrs.update({'rows': '2', 'placeholder': 'Description'})


class WorkorderNewItemForm(forms.ModelForm):
    class Meta:
       model = WorkorderItem
       fields = ['item_category', 'item_subcategory', 'description']

class WorkorderItemForm(forms.ModelForm):
   class Meta:
       model = WorkorderItem
       fields = ['internal_company', 'design_type', 'description', 'quantity', 'unit_price', 'total_price', 'last_item_order', 'last_item_price']

class DesignItemForm(forms.ModelForm):
   class Meta:
       model = WorkorderItem
       fields = ['internal_company', 'design_type', 'description', 'quantity', 'unit_price', 'last_item_order', 'last_item_price']
       labels = {
            'unit_price':'Price per Hour',

        }
       
class PostageItemForm(forms.ModelForm):
   class Meta:
       model = WorkorderItem
       fields = ['internal_company', 'description', 'quantity', 'unit_price']
       labels = {
            'unit_price':'Price each',

        }
       
class CustomItemForm(forms.ModelForm):
   class Meta:
       model = WorkorderItem
       fields = ['internal_company', 'description', 'quantity', 'unit_price', 'last_item_order', 'last_item_price']
       labels = {
            'unit_price':'Price per piece',

        }
       
class AddSetPriceCategoryForm(forms.ModelForm):
   class Meta:
       model = WorkorderItem
       fields = ['internal_company', 'description', 'quantity', 'unit_price', 'last_item_order', 'last_item_price']
       labels = {
            'unit_price':'Price per piece',

        }

class NoteForm(forms.ModelForm):
    class Meta:
        model = WorkorderItem
        fields = ['notes', 'show_notes']
        labels = {
            'show_notes':'Show notes on pdf invoice',

        }

class JobStatusForm(forms.ModelForm):
    class Meta:
        model = WorkorderItem
        fields = ['job_status', 'assigned_user', 'assigned_group', 'completed']
        labels = {

        }

class WorkorderNoteForm(forms.ModelForm):
    class Meta:
        model = Workorder
        fields = ['notes', 'show_notes']
        labels = {
            'show_notes':'Show notes on pdf invoice',

        }

class ParentItemForm(forms.ModelForm):
    class Meta:
        model = WorkorderItem
        fields = ['description', 'quantity', 'parent_item', 'parent', 'added_to_parent']