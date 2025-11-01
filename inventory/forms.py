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
       fields = ['name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'website', 'supplier', 'retail_vendor', 'inventory_vendor', 'non_inventory_vendor', 'online_store_vendor']
       labels = {
        }
       

   def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make optional for tests’ “minimal fields”
        for f in ["state", "zipcode", "phone1", "phone2", "email", "website"]:
            if f in self.fields:
                self.fields[f].required = False
       
class InventoryMasterForm(forms.ModelForm):
    class Meta:
        model = InventoryMaster
        fields = ['name', 'description', 'primary_vendor', 'primary_vendor_part_number', 'primary_base_unit', 'units_per_base_unit', 'unit_cost', 'supplies', 'retail', 'non_inventory', 'online_store']
        labels = {
        } 

class VendorItemDetailForm(forms.ModelForm):
    class Meta:
        model = VendorItemDetail
        fields = ['name', 'vendor_part_number', 'description', 'internal_part_number', 'supplies', 'retail', 'non_inventory', 'online_store']
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
       

class MergeItemsForm(forms.Form):
    target = forms.ModelChoiceField(
        queryset=InventoryMaster.objects.filter(is_active=True),
        label="Keep (target)",
        help_text="The canonical item to keep"
    )
    duplicates = forms.ModelMultipleChoiceField(
        queryset=InventoryMaster.objects.filter(is_active=True),
        help_text="Select one or more duplicates to merge into the target",
        label="Merge these into target"
    )
    prefer_target_name = forms.BooleanField(required=False, initial=True,
        help_text="If unchecked and target.name is blank, we’ll borrow a non-blank name from duplicates.")
       
class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ["name", "supplier", "retail_vendor", "inventory_vendor",
                  "non_inventory_vendor", "email", "website", "city", "state", "active"]
        
class AddItemtoListForm(forms.Form):
    # Hidden ids (the template already includes a hidden master_id input; keeping item_id here)
    item_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    # Core data
    quantity = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        label="Qty",
    )

    # Fields referenced in the template
    inventory_category = forms.ChoiceField(
        required=False,
        label="Inventory Category",
        choices=(),   # optionally populate in __init__
    )
    retail_item = forms.BooleanField(
        required=False,
        label="Retail Item",
    )

    # “Type” toggles
    type_paper = forms.BooleanField(required=False, label="Paper")
    type_envelope = forms.BooleanField(required=False, label="Envelope")
    type_wideformat = forms.BooleanField(required=False, label="Wide Format")
    type_vinyl = forms.BooleanField(required=False, label="Vinyl")
    type_mask = forms.BooleanField(required=False, label="Mask")
    type_laminate = forms.BooleanField(required=False, label="Laminate")
    type_substrate = forms.BooleanField(required=False, label="Substrate")

    def __init__(self, *args, **kwargs):
        # Optionally accept categories via kwargs to keep it generic/testable
        categories = kwargs.pop("category_choices", None)
        super().__init__(*args, **kwargs)
        if categories is not None:
            self.fields["inventory_category"].choices = categories

class InventoryMasterDetailsForm(forms.ModelForm):
    # extra (non-model) fields
    type_paper     = forms.BooleanField(required=False)
    type_envelope  = forms.BooleanField(required=False)
    type_wideformat= forms.BooleanField(required=False)
    type_vinyl     = forms.BooleanField(required=False)
    type_mask      = forms.BooleanField(required=False)
    type_laminate  = forms.BooleanField(required=False)
    type_substrate = forms.BooleanField(required=False)
    retail_item    = forms.BooleanField(required=False)
    # inventory_category = forms.ModelChoiceField(...)

    class Meta:
        model = InventoryMaster
        fields = []  # <-- IMPORTANT: do NOT include the non-model field names

    def save(self, commit=True):
        """
        If you eventually want to persist these to real model fields
        or a related model, do it here. For now, it's a no-op.
        """
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
    