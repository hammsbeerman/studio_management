from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.db.models.functions import Lower
from .models import OrderOut, SetPrice, Photography, Vendor, InventoryMaster, VendorItemDetail
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from localflavor.us.forms import USStateSelect
from decimal import Decimal
from controls.models import RetailInventoryCategory, Measurement



class AddVendorForm(forms.ModelForm):
   state = forms.CharField(widget=USStateSelect(), initial='WI')
   class Meta:
       model = Vendor
       fields = ['name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'website', 'supplier', 'retail_vendor', 'inventory_vendor', 'non_inventory_vendor', 'online_store_vendor']
       labels = {
        }
       
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

class RetailCategoryForm(forms.ModelForm):
    class Meta:
        model = RetailInventoryCategory
        fields = ["name", "default_markup_percent", "default_markup_flat"]


class RetailCategoryMarkupForm(forms.ModelForm):
    class Meta:
        model = RetailInventoryCategory
        fields = ["default_markup_percent", "default_markup_flat"]
        widgets = {
            "default_markup_percent": forms.NumberInput(attrs={"step": "0.01"}),
            "default_markup_flat": forms.NumberInput(attrs={"step": "0.01"}),
        }


class InventoryItemPricingForm(forms.ModelForm):
    class Meta:
        model = InventoryMaster
        fields = [
            "retail_category",
            "retail_price",          # hard override
            "retail_markup_percent",
            "retail_markup_flat",
        ]
        widgets = {
            "retail_price": forms.NumberInput(attrs={"step": "0.01"}),
            "retail_markup_percent": forms.NumberInput(attrs={"step": "0.01"}),
            "retail_markup_flat": forms.NumberInput(attrs={"step": "0.01"}),
        }

class InventoryAdjustmentForm(forms.Form):
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryMaster.objects.order_by("name"),
        label="Item",
        widget=forms.Select(
            attrs={
                "class": "form-select select2",  # <-- use your global select2 class
            }
        ),
    )
    qty_delta = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Quantity change",
        help_text="Use positive to add stock, negative to remove stock.",
    )
    note = forms.CharField(
        label="Reason / note",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def clean_qty_delta(self):
        v = self.cleaned_data["qty_delta"]
        if v == 0:
            raise forms.ValidationError("Quantity change cannot be zero.")
        return v

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inventory_item"].empty_label = "Search item…"

    def label_from_instance(self, obj: InventoryMaster) -> str:
        parts = [obj.name or ""]

        pn = getattr(obj, "primary_vendor_part_number", "") or getattr(obj, "part_number", "")
        if pn:
            parts.append(f"PN: {pn}")

        sku = getattr(obj, "internal_part_number", "")
        if sku:
            parts.append(f"SKU: {sku}")

        desc = getattr(obj, "description", "")
        if desc and desc not in parts[0]:
            parts.append(desc)

        return " — ".join([p for p in parts if p])
       

class BulkUomUpdateForm(forms.Form):
    measurement = forms.ModelChoiceField(queryset=Measurement.objects.order_by("name"))
    variation_qty = forms.DecimalField(initial=Decimal("1.0000"), max_digits=12, decimal_places=4)

    name_contains = forms.CharField(required=False)
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.order_by("name"), required=False)

    set_as_base = forms.BooleanField(required=False)
    set_as_default_sell = forms.BooleanField(required=False)
    set_as_default_receive = forms.BooleanField(required=False)

    apply = forms.BooleanField(required=False, help_text="If unchecked, this is a dry-run preview.")

class NormalizeMeasurementsForm(forms.Form):
    only_active = forms.BooleanField(required=False, initial=True)
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.all().order_by("name"), required=False)
    name_contains = forms.CharField(required=False)

    do_each = forms.BooleanField(required=False, initial=True, label="Normalize Ea → Each")
    do_sht = forms.BooleanField(required=False, initial=True, label="Normalize Sheet/Sheets → Sht")

    include_primary_base_unit = forms.BooleanField(
        required=False,
        initial=True,
        label="Also normalize InventoryMaster.primary_base_unit",
    )

    # ✅ NEW (guardrails)
    fix_missing_base_uom = forms.BooleanField(
        required=False,
        initial=False,
        label="Fix missing Base UOM (set base = Each × 1.0000 if missing)",
        help_text="Only touches items that have no base flagged in variations.",
    )
    fix_missing_defaults = forms.BooleanField(
        required=False,
        initial=False,
        label="Fix missing Default Sell/Receive (use base UOM)",
        help_text="Retail gets default sell; supplies gets default receive (only if missing).",
    )

    apply = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Check to APPLY changes (otherwise this is a dry run).",
    )


class UomAuditFilterForm(forms.Form):
    only_active = forms.BooleanField(required=False, initial=True)
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.all().order_by("name"), required=False)
    name_contains = forms.CharField(required=False)

class UomFixActionForm(forms.Form):
    item_id = forms.IntegerField()
    variation_id = forms.IntegerField(required=False)
    action = forms.ChoiceField(choices=[
        ("set_base", "Set Base UOM"),
        ("set_default_sell", "Set Default Sell UOM"),
        ("set_default_receive", "Set Default Receive UOM"),
        ("normalize_defaults", "Normalize Missing Defaults"),
    ])

class UomSetTripleForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput)

    # Pick Measurement + qty for each role (optional)
    base_measurement = forms.ModelChoiceField(
        queryset=Measurement.objects.order_by("name"),
        required=False,
        empty_label="— no change —",
        label="Base UOM",
    )
    base_qty = forms.DecimalField(
        required=False,
        initial=Decimal("1.0000"),
        max_digits=12,
        decimal_places=4,
        label="Base qty",
    )

    sell_measurement = forms.ModelChoiceField(
        queryset=Measurement.objects.order_by("name"),
        required=False,
        empty_label="— no change —",
        label="Default Sell UOM",
    )
    sell_qty = forms.DecimalField(
        required=False,
        initial=Decimal("1.0000"),
        max_digits=12,
        decimal_places=4,
        label="Sell qty",
    )

    receive_measurement = forms.ModelChoiceField(
        queryset=Measurement.objects.order_by("name"),
        required=False,
        empty_label="— no change —",
        label="Default Receive UOM",
    )
    receive_qty = forms.DecimalField(
        required=False,
        initial=Decimal("1.0000"),
        max_digits=12,
        decimal_places=4,
        label="Receive qty",
    )