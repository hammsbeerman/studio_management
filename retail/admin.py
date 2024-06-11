from django.contrib import admin
from .models import RetailInventory


class RetailInventoryAdmin(admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['created', 'updated']
    list_display = ('paper_item', 'description')
    #fields = ['name',]

admin.site.register(RetailInventory, RetailInventoryAdmin)