from django.contrib import admin, messages
from django.db.models import F
from django.apps import apps

from .models import (
    Numbering,
    FixedCost,
    Category,
    SubCategory,
    DesignType,
    Measurement,
    SetPriceCategory,
    SetPriceItemPrice,
    InventoryCategory,
    JobStatus,
    UserGroup,
    PaymentType,
    RetailInventoryCategory,
    RetailInventorySubCategory,
    GroupCategory,
)

# -----------------------------
# Actions
# -----------------------------

@admin.action(description="Increment selected counters by 1")
def numbering_bump_1(modeladmin, request, queryset):
    updated = queryset.update(value=F("value") + 1)
    messages.success(request, f"Bumped {updated} counter(s) by 1.")

@admin.action(description="Increment selected counters by 10")
def numbering_bump_10(modeladmin, request, queryset):
    updated = queryset.update(value=F("value") + 10)
    messages.success(request, f"Bumped {updated} counter(s) by 10.")

@admin.action(description="Mark selected as Active")
def mark_active(modeladmin, request, queryset):
    updated = queryset.update(active=True)
    messages.success(request, f"Set {updated} item(s) active.")

@admin.action(description="Mark selected as Inactive")
def mark_inactive(modeladmin, request, queryset):
    updated = queryset.update(active=False)
    messages.success(request, f"Set {updated} item(s) inactive.")


# -----------------------------
# Admin registrations
# -----------------------------

@admin.register(Numbering)
class NumberingAdmin(admin.ModelAdmin):
    list_display = ("name", "value")
    list_editable = ("value",)
    search_fields = ("name",)
    actions = [numbering_bump_1, numbering_bump_10]


class CategorySubcategoryInline(admin.StackedInline):
    model = SubCategory
    extra = 0
    fields = ("name", "description", "template", "set_price", "setprice_name", "inventory_category")
    autocomplete_fields = ("inventory_category",)


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategorySubcategoryInline]
    list_display = (
        "name",
        "description",
        "design_type",
        "formname",
        "modelname",
        "modal",
        "template",
        "setprice",
        "wideformat",
        "inventory_category",
        "pricesheet_type",
        "active",
    )
    list_filter = (
        "active",
        "wideformat",
        "setprice",
        "template",
        "modal",
        "inventory_category",
        "pricesheet_type",
    )
    search_fields = ("name", "description", "material_type", "formname", "modelname")
    autocomplete_fields = ("pricesheet_type", "inventory_category")
    list_per_page = 25


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "inventory_category", "template", "set_price")
    list_filter = ("template", "set_price", "category", "inventory_category")
    search_fields = ("name", "description")
    autocomplete_fields = ("category", "inventory_category")
    list_per_page = 25


@admin.register(FixedCost)
class FixedCostAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "create_workorder",
        "reclaim_artwork",
        "send_to_press",
        "send_mailmerge_to_press",
        "material_markup",
        "wear_and_tear",
        "trim_to_size",
        "duplo_1",
        "duplo_2",
        "duplo_3",
        "ncr_compound",
        "pad_compound",
    )
    search_fields = ("name",)


@admin.register(DesignType)
class DesignTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SetPriceCategory)
class SetPriceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "created", "updated")
    list_filter = ("category",)
    search_fields = ("name",)
    autocomplete_fields = ("category",)
    readonly_fields = ("created", "updated")


@admin.register(SetPriceItemPrice)
class SetPriceItemPriceAdmin(admin.ModelAdmin):
    list_display = ("description", "name", "set_quantity", "price", "created", "updated")
    list_filter = ("name",)
    search_fields = ("description",)
    autocomplete_fields = ("name",)
    readonly_fields = ("created", "updated")
    list_per_page = 25


@admin.register(JobStatus)
class JobStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "workorder_type", "workorder_item_type")
    list_filter = ("workorder_type", "workorder_item_type")
    search_fields = ("name",)


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "detail_field")
    search_fields = ("name", "detail_field")


@admin.register(GroupCategory)
class GroupCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(RetailInventoryCategory)
class RetailInventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "active")
    list_filter = ("active",)
    search_fields = ("name", "parent")
    actions = [mark_active, mark_inactive]


@admin.register(RetailInventorySubCategory)
class RetailInventorySubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active", "inventory_category")
    search_fields = ("name", "description")
    filter_horizontal = ("inventory_category",)
    actions = [mark_active, mark_inactive]