# inventory/admin.py
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django import forms
from import_export.admin import ImportExportModelAdmin
from decimal import Decimal
from controls.models import Measurement

from .models import (
    Inventory,
    Vendor,
    VendorContact,
    Photography,
    OrderOut,
    SetPrice,
    InventoryMaster,
    VendorItemDetail,
    InventoryPricingGroup,
    InventoryQtyVariations,
    #InventoryItem,
)

from controls.models import GroupCategory

class InventoryPricingGroupInline(admin.TabularInline):
    model = InventoryPricingGroup
    extra = 1
    autocomplete_fields = ('group',)  # make sure GroupCategoryAdmin has search_fields

# Single action form usable by multiple actions
class InventoryMasterActionForm(ActionForm):
    action = forms.ChoiceField(required=False)  # Django will set choices later
    select_across = forms.BooleanField(required=False, initial=0, widget=forms.HiddenInput)
    group  = forms.ModelChoiceField(queryset=GroupCategory.objects.all(), required=False, label="Group")
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.all(), required=False, label="Set primary vendor to")
    vendor_part_number = forms.CharField(required=False, label="Vendor part #")
    base_unit = forms.ModelChoiceField(queryset=Measurement.objects.all(), required=False, label="Set base unit to")
    base_qty  = forms.DecimalField(required=False, label="Units per base", max_digits=15, decimal_places=6)
    bulk_set_active = forms.BooleanField(
        required=False, label="Set active?"
    )
    pass

# ---------- Vendor ----------
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "supplier",
        "retail_vendor",
        "inventory_vendor",
        "non_inventory_vendor",
        "active",
    )
    list_filter = (
        "supplier",
        "retail_vendor",
        "inventory_vendor",
        "non_inventory_vendor",
        "active",
    )
    search_fields = ("name", "email", "website", "city", "state")
    ordering = ("name",)
    readonly_fields = ("created", "updated")


@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ("fname", "lname", "vendor", "email", "phone1", "updated")
    list_filter = ("vendor",)
    search_fields = ("fname", "lname", "email", "vendor__name")
    autocomplete_fields = ("vendor",)
    ordering = ("lname", "fname")




@admin.register(InventoryMaster)
class InventoryMasterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "primary_vendor",
        "primary_vendor_part_number",
        "primary_base_unit",
        "units_per_base_unit",
        "unit_cost",
        "price_per_m",
        "high_price",
        "supplies",
        "retail",
        "non_inventory",
        "online_store",
        "grouped",
        "not_grouped",
        "updated",
    )
    list_filter = (
        "supplies",
        "retail",
        "non_inventory",
        "online_store",
        "grouped",
        "not_grouped",
        "primary_vendor",
        "primary_base_unit",
    )
    search_fields = (
        "name",
        "description",
        "primary_vendor_part_number",
        "primary_vendor__name",
    )
    readonly_fields = ("created", "updated")
    list_select_related = ("primary_vendor", "primary_base_unit")
    date_hierarchy = "updated"
    ordering = ("name",)
    actions = ["bulk_add_to_group", "bulk_set_primary_vendor", "bulk_recompute_pricing", "bulk_mark_not_grouped", "action_set_primary_vendor", "action_set_base_unit", "action_ensure_base_variation", "action_update_high_price", "set_group", "set_vendor", "bulk_set_active"]
    action_form = InventoryMasterActionForm
    inlines = [InventoryPricingGroupInline]

    def bulk_add_to_group(self, request, queryset):
        group = self.action_form.cleaned_data.get("group") if hasattr(self, "action_form") else None
        if not group:
            self.message_user(request, "Please choose a Group in the action form.", level=messages.ERROR)
            return
        count = 0
        for obj in queryset:
            obj.add_to_price_group(group)  # uses your model helper
            count += 1
        self.message_user(request, f"Added {count} items to group '{group.name}'.")

    bulk_add_to_group.short_description = "Add selected items to Group (choose in form)"

    def bulk_set_primary_vendor(self, request, queryset):
        vendor = self.action_form.cleaned_data.get("vendor") if hasattr(self, "action_form") else None
        if not vendor:
            self.message_user(request, "Please choose a Vendor in the action form.", level=messages.ERROR)
            return
        count = 0
        for obj in queryset:
            obj.set_primary_vendor(vendor)  # model helper creates VendorItemDetail if missing
            count += 1
        self.message_user(request, f"Set primary vendor to '{vendor.name}' for {count} items.")

    bulk_set_primary_vendor.short_description = "Set Primary Vendor (choose in form)"

    def bulk_recompute_pricing(self, request, queryset):
        count = 0
        for obj in queryset:
            obj.update_high_price_from_invoices()  # updates high_price
            # (post_save signal will compute unit_cost/price_per_m and sync shadow Inventory)
            count += 1
        self.message_user(request, f"Recomputed pricing for {count} items.")

    bulk_recompute_pricing.short_description = "Recompute pricing from invoices"

    def bulk_mark_not_grouped(self, request, queryset):
        updated = queryset.update(not_grouped=True, grouped=False)
        self.message_user(request, f"Marked {updated} items as NOT grouped.")

    bulk_mark_not_grouped.short_description = "Mark as Not Grouped"

    def action_set_primary_vendor(self, request, queryset):
        vendor_id = request.POST.get("vendor")  # comes from the action form
        vpn = request.POST.get("vendor_part_number") or None
        if not vendor_id:
            self.message_user(request, "No vendor selected in action form.", level="warning")
            return
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
        except Vendor.DoesNotExist:
            self.message_user(request, "Selected vendor does not exist.", level="error")
            return

        updated = 0
        for obj in queryset:
            obj.set_primary_vendor(vendor, vendor_part_number=vpn)
            updated += 1
        self.message_user(request, f"Primary vendor set on {updated} item(s).")

    action_set_primary_vendor.short_description = "Set primary vendor (uses action form fields)"

    def action_set_base_unit(self, request, queryset):
        base_unit_id = request.POST.get("base_unit")
        base_qty = request.POST.get("base_qty")

        if not base_unit_id:
            self.message_user(request, "No base unit selected.", level=messages.WARNING)
            return

        try:
            unit = Measurement.objects.get(pk=base_unit_id)
        except Measurement.DoesNotExist:
            self.message_user(request, "Selected base unit not found.", level=messages.ERROR)
            return

        # base_qty may be empty; default to None so helper methods can decide.
        qty = None
        if base_qty:
            try:
                qty = float(base_qty)
            except ValueError:
                self.message_user(request, "Invalid base quantity.", level=messages.ERROR)
                return

        changed = 0
        for item in queryset:
            # Prefer your helper (ensures InventoryQtyVariations etc.)
            if hasattr(item, "set_primary_base_unit"):
                item.set_primary_base_unit(unit, qty=qty)
            else:
                # Fallback to direct fields if helper missing
                if hasattr(item, "primary_base_unit"):
                    item.primary_base_unit = unit
                if qty is not None and hasattr(item, "units_per_base_unit"):
                    item.units_per_base_unit = qty
                item.save()

                # If you rely on a “base variation”, try to ensure it
                if hasattr(item, "ensure_base_variation"):
                    item.ensure_base_variation()

            changed += 1

        self.message_user(
            request,
            f"Updated base unit/qty on {changed} item(s).",
            level=messages.SUCCESS,
        )
    action_set_base_unit.short_description = "Set Base Unit & Qty (from action form)"

    def action_ensure_base_variation(self, request, queryset):
        created_count = 0
        for obj in queryset:
            if obj.ensure_base_variation():
                created_count += 1
        self.message_user(request, f"Ensured base variation. Created {created_count} new variation(s).")

    action_ensure_base_variation.short_description = "Ensure base variation exists"

    def action_update_high_price(self, request, queryset):
        updated = 0
        for obj in queryset:
            val = obj.update_high_price_from_invoices()
            if val is not None:
                updated += 1
        self.message_user(request, f"Updated high_price from invoices for {updated} item(s).")

    action_update_high_price.short_description = "Update high_price from invoices"

    def action_set_group(self, request, queryset):
        group_id = request.POST.get("group")  # from action form
        if not group_id:
            self.message_user(request, "No group selected.", level=messages.WARNING)
            return
        try:
            group = GroupCategory.objects.get(pk=group_id)
        except GroupCategory.DoesNotExist:
            self.message_user(request, "Selected group not found.", level=messages.ERROR)
            return

        updated = queryset.update(group=group)
        self.message_user(
            request, f"Updated group on {updated} item(s).", level=messages.SUCCESS
        )
    action_set_group.short_description = "Set Group (from action form)"

    def action_set_vendor(self, request, queryset):
        vendor_id = request.POST.get("vendor")
        vendor_part_number = request.POST.get("vendor_part_number", "").strip()

        if not vendor_id and not vendor_part_number:
            self.message_user(
                request,
                "Choose a vendor and/or enter a vendor part #.",
                level=messages.WARNING,
            )
            return

        vendor = None
        if vendor_id:
            try:
                vendor = Vendor.objects.get(pk=vendor_id)
            except Vendor.DoesNotExist:
                self.message_user(request, "Selected vendor not found.", level=messages.ERROR)
                return

        count = 0
        for item in queryset:
            # If you have a canonical “primary vendor” field or relation, set it here.
            if vendor:
                # Prefer a method if you’ve got one
                if hasattr(item, "set_primary_vendor"):
                    item.set_primary_vendor(vendor, vendor_part_number or None)
                else:
                    # Fallback: set fields directly if they exist on the model
                    if hasattr(item, "primary_vendor"):
                        item.primary_vendor = vendor
                    if vendor_part_number and hasattr(item, "vendor_part_number"):
                        item.vendor_part_number = vendor_part_number
                    item.save(update_fields=[
                        f for f in ["primary_vendor", "vendor_part_number"]
                        if hasattr(item, f)
                    ])
            elif vendor_part_number and hasattr(item, "vendor_part_number"):
                item.vendor_part_number = vendor_part_number
                item.save(update_fields=["vendor_part_number"])
            count += 1

        self.message_user(
            request, f"Updated vendor info on {count} item(s).", level=messages.SUCCESS
        )
    action_set_vendor.short_description = "Set Primary Vendor / Part # (from action form)"

    def action_bulk_set_active(self, request, queryset):
        flag = request.POST.get("bulk_set_active")
        # Checkbox sends "on" if checked; empty/absent if not.
        if not flag:
            self.message_user(request, "Checkbox ‘Set active?’ was not checked.", level=messages.INFO)
            return

        # Only update if the model has `is_active` or `active` boolean
        fields = []
        if hasattr(InventoryMaster, "is_active"):
            updated = queryset.update(is_active=True)
            fields.append("is_active")
        elif hasattr(InventoryMaster, "active"):
            updated = queryset.update(active=True)
            fields.append("active")
        else:
            self.message_user(
                request,
                "No ‘active’ field found on InventoryMaster.",
                level=messages.ERROR,
            )
            return

        self.message_user(
            request, f"Set active on {updated} item(s).", level=messages.SUCCESS
        )
    action_bulk_set_active.short_description = "Activate selected items"


# ---------- Flat Inventory (keeps ImportExport) ----------
@admin.register(Inventory)
class InventoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    readonly_fields = ("created", "updated")
    list_display = (
        "name",
        "internal_part_number",
        "unit_cost",
        "price_per_m",
        "measurement",
        "retail_item",
        "updated",
    )
    list_filter = ("retail_item", "type_paper", "type_envelope", "type_wideformat",
                   "type_vinyl", "type_mask", "type_laminate", "type_substrate")
    search_fields = (
        "name",
        "name2",
        "description",
        "vendor_part_number",
        "internal_part_number__name",
    )
    autocomplete_fields = (
        "internal_part_number",
        "measurement",
        "width_measurement",
        "length_measurement",
        "inventory_category",
    )
    filter_horizontal = ("inventory_category",)
    list_select_related = ("internal_part_number", "measurement")
    date_hierarchy = "updated"
    ordering = ("name",)


# ---------- Variations ----------
@admin.register(InventoryQtyVariations)
class InventoryQtyVariationsAdmin(admin.ModelAdmin):
    list_display = ("inventory", "variation", "variation_qty")
    list_filter = ("variation",)
    search_fields = ("inventory__name", "variation__name")
    autocomplete_fields = ("inventory", "variation")
    list_select_related = ("inventory", "variation")


# ---------- Pricing Groups ----------
@admin.register(InventoryPricingGroup)
class InventoryPricingGroupAdmin(admin.ModelAdmin):
    list_display = ("inventory", "group", "high_price")
    list_filter = ("group",)
    search_fields = ("inventory__name", "group__name")
    autocomplete_fields = ("inventory", "group")
    list_select_related = ("inventory", "group")


# ---------- Vendor Item Detail ----------
@admin.register(VendorItemDetail)
class VendorItemDetailAdmin(admin.ModelAdmin):
    list_display = ("internal_part_number", "vendor", "vendor_part_number", "high_price", "updated")
    list_filter = ("vendor",)
    search_fields = ("internal_part_number__name", "vendor__name", "vendor_part_number")
    autocomplete_fields = ("internal_part_number", "vendor")
    list_select_related = ("internal_part_number", "vendor")
    date_hierarchy = "updated"


# ---------- Orders Out ----------
@admin.register(OrderOut)
class OrderOutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dateentered",
        "vendor",
        "customer",
        "open",
        "billed",
        "quantity",
        "purchase_price",
        "unit_price",
        "total_price",
        "internal_company",
    )
    list_filter = ("open", "billed", "internal_company", "vendor")
    search_fields = ("id", "hr_workorder", "hr_customer", "description", "vendor__name", "customer__company_name")
    autocomplete_fields = ("vendor", "customer", "workorder")
    list_select_related = ("vendor", "customer", "workorder")
    date_hierarchy = "dateentered"
    ordering = ("-dateentered",)
    actions = ["mark_billed", "mark_open"]

    def mark_billed(self, request, queryset):
        updated = queryset.update(billed=True, open=False)
        self.message_user(request, f"Marked {updated} orders as billed.")
    mark_billed.short_description = "Mark selected orders as billed"

    def mark_open(self, request, queryset):
        updated = queryset.update(open=True, billed=False)
        self.message_user(request, f"Marked {updated} orders as open.")
    mark_open.short_description = "Mark selected orders as open"


# ---------- SetPrice / Photography ----------
@admin.register(SetPrice)
class SetPriceAdmin(admin.ModelAdmin):
    list_display = ("workorder", "customer", "quantity", "unit_price", "total_price", "billed", "dateentered")
    list_filter = ("billed", "internal_company")
    search_fields = ("workorder__workorder", "hr_customer", "description")
    autocomplete_fields = ("workorder", "customer", "paper_stock")
    date_hierarchy = "dateentered"


@admin.register(Photography)
class PhotographyAdmin(admin.ModelAdmin):
    list_display = ("workorder", "customer", "quantity", "unit_price", "total_price", "billed", "dateentered")
    list_filter = ("billed", "internal_company")
    search_fields = ("workorder__workorder", "hr_customer", "description")
    autocomplete_fields = ("workorder", "customer")
    date_hierarchy = "dateentered"


# @admin.register(InventoryItem)
# class InventoryItemAdmin(admin.ModelAdmin):
#     list_filter = ["is_active", "merged_into"]
#     # default changelist to active only
#     def get_queryset(self, request):
#         return super().get_queryset(request).filter(is_active=True)



