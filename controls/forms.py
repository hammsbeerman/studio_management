from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy

from .models import SubCategory, Category, SetPriceCategory, SetPriceItemPrice
from inventory.models import InventoryPricingGroup, Inventory

# If you don't actually use crispy in these forms, you can remove these imports.
from crispy_forms.helper import FormHelper  # noqa: F401
from crispy_forms.layout import Submit  # noqa: F401


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ["category", "name", "description", "inventory_category"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "design_type", "formname", "modal"]


class AddSetPriceCategoryForm(forms.ModelForm):
    class Meta:
        model = SetPriceCategory
        fields = ["name", "category", "updated"]
        labels = {}


class AddSetPriceItemForm(forms.ModelForm):
    class Meta:
        model = SetPriceItemPrice
        fields = ["name", "description", "set_quantity", "price", "updated"]
        labels = {
            "name": "Group",
        }


class AddInventoryPricingGroupForm(forms.ModelForm):
    class Meta:
        model = InventoryPricingGroup
        fields = ["inventory", "group"]


class AddItemtoListForm(forms.ModelForm):
    """
    Tests expect an empty POST to be invalid.
    We require at least one type flag OR a category to be selected.
    """

    class Meta:
        model = Inventory
        fields = [
            "type_paper",
            "type_envelope",
            "type_wideformat",
            "type_vinyl",
            "type_mask",
            "type_laminate",
            "type_substrate",
            "inventory_category",
            "retail_item",
        ]
        widgets = {
            "inventory_category": forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned = super().clean()

        bool_fields = [
            "type_paper",
            "type_envelope",
            "type_wideformat",
            "type_vinyl",
            "type_mask",
            "type_laminate",
            "type_substrate",
            "retail_item",
        ]
        any_checked = any(bool(cleaned.get(f)) for f in bool_fields)
        has_category = bool(cleaned.get("inventory_category"))

        if not any_checked and not has_category:
            raise forms.ValidationError(
                "Select at least one item type or an inventory category."
            )

        return cleaned