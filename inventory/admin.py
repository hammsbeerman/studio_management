from django.contrib import admin
from .models import Inventory, Vendor, OrderOut, SetPrice, InventoryCategory, InventoryMaster, VendorItemDetail
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

admin.site.register(InventoryMaster)

admin.site.register(VendorItemDetail)
