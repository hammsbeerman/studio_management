from django.contrib import admin
from .models import Inventory, Vendor, OrderOut, SetPrice, InventoryCategory, InventoryMaster, InventoryRetailPrice, VendorItemDetail, InventoryPricingGroup, InventoryQtyVariations #ItemQtyVariations
from import_export.admin import ImportExportModelAdmin



# class InventoryVendorInline(admin.StackedInline):
#     model = Vendor
#     extra = 0
#     #readonly_fields = ['created', 'updated']

class InventoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['created', 'updated']
    list_display = ('name', 'description')
    #fields = ['name',]

admin.site.register(Inventory, InventoryAdmin)

class InventoryDetailAdmin(admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    #readonly_fields = ['created', 'updated']
    list_display = ('item','vendor', 'vendor_item_number')
    #fields = ['name',]

#admin.site.register(InventoryDetail, InventoryDetailAdmin)

# class InventoryVendorInline(admin.StackedInline):
#     model = Vendor
#     extra = 0
#     #readonly_fields = ['created', 'updated']

class VendorAdmin(admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['created', 'updated']
    list_display = ('name',)
    #fields = ['name', 'category', 'description']

admin.site.register(Vendor, VendorAdmin)


class OrderOutAdmin(admin.ModelAdmin):
    list_display = ['workorder', 'customer', 'description', 'quantity', 'total_price']

admin.site.register(OrderOut, OrderOutAdmin)

admin.site.register(SetPrice)

# class InventoryCategoryAdmin(admin.ModelAdmin):
#     #inlines = [InventoryVendorInline]
#     #readonly_fields = ['created', 'updated']
#     list_display = ('item', 'category')
#     #fields = ['name',]

# admin.site.register(InventoryCategory, InventoryCategoryAdmin)

class InventoryRetailPriceInline(admin.StackedInline):
    model = InventoryRetailPrice
    extra = 0
    can_delete = False

@admin.register(InventoryMaster)
class InventoryMasterAdmin(ImportExportModelAdmin):
    inlines = [InventoryRetailPriceInline]
    list_display = (
        "name",
        "unit_cost",
        "retail_price",
        "retail_markup_percent",
        "retail_markup_flat",
        "retail_category",
    )
    search_fields = ("name", "primary_vendor_part_number")
    list_filter = ("retail_category",)

admin.site.register(VendorItemDetail)

admin.site.register(InventoryQtyVariations)

admin.site.register(InventoryPricingGroup)

# admin.site.register(ItemQtyVariations)

#admin.site.register(ItemPricingGroup)

@admin.register(InventoryRetailPrice)
class InventoryRetailPriceAdmin(admin.ModelAdmin):
    list_select_related = ("inventory", "inventory__primary_vendor", "inventory__retail_category")
    list_display = (
        "inventory_name",
        "primary_vendor_name",
        "retail_category_name",
        "purchase_price",
        "calculated_price",
        "override_price",
        "effective_price",
        "updated_at",
    )
    search_fields = (
        "inventory__name",
        "inventory__primary_vendor_part_number",
        "inventory__primary_vendor__name",
    )
    list_filter = ("inventory__retail_category",)

    def inventory_name(self, obj):
        return obj.inventory.name
    inventory_name.admin_order_field = "inventory__name"
    inventory_name.short_description = "Item"

    def primary_vendor_name(self, obj):
        vendor = obj.inventory.primary_vendor
        return vendor.name if vendor else ""
    primary_vendor_name.short_description = "Vendor"

    def retail_category_name(self, obj):
        cat = obj.inventory.retail_category
        return cat.name if cat else ""
    retail_category_name.short_description = "Retail Category"

    def effective_price(self, obj):
        return obj.effective_price
    effective_price.short_description = "Effective Price"
