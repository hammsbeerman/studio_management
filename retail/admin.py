from django.contrib import admin
from .models import RetailVendorItemDetail, RetailInventoryMaster, RetailInvoiceItem


class RetailInventoryAdmin(admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['created', 'updated']
    list_display = ('name', 'description')
    #fields = ['name',]

#admin.site.register(RetailInventory, RetailInventoryAdmin)

admin.site.register(RetailVendorItemDetail)

admin.site.register(RetailInventoryMaster)

admin.site.register(RetailInvoiceItem)

#admin.site.register(RetailVendor)

#admin.site.register(RetailInvoices)