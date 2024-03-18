from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import SubCategory, Category
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

