from django.contrib import admin
from .models import Inventory, Vendor, InventoryDetail, Measurement



# class InventoryVendorInline(admin.StackedInline):
#     model = Vendor
#     extra = 0
#     #readonly_fields = ['created', 'updated']

class InventoryAdmin(admin.ModelAdmin):
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

admin.site.register(InventoryDetail, InventoryDetailAdmin)

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

admin.site.register(Measurement)
