from django.contrib import admin

from .models import Workorder, WorkorderItem#ItemCategory, 


class WorkorderAdmin(admin.ModelAdmin):
    fields = ['customer', 'workorder', 'internal_company', 'description', 'deadline', 'budget', 'quoted_price', 'original_order', 'billed', 'notes', 'completed', 'total_balance', 'amount_paid', 'open_balance', 'paid_in_full']
    list_display = ('customer', 'workorder', 'internal_company', 'description', 'deadline', 'budget', 'quoted_price', 'quote_number', 'original_order', 'billed', 'total_balance', 'amount_paid', 'open_balance')

admin.site.register(Workorder, WorkorderAdmin)




# class ItemCategoryAdmin(admin.ModelAdmin):
#    #extra = 0
#    # readonly_fields = ['created', 'updated']
#     fields = ['workorder', 'description', 'category', 'internal_company']
#     ordering = ('-workorder',)

# admin.site.register(ItemCategory, ItemCategoryAdmin)


class WorkorderItemAdmin(admin.ModelAdmin):
    list_display = ('workorder', 'item_category', 'design_type', 'description', 'quantity', 'unit_price', 'total_price', 'created', 'updated')

admin.site.register(WorkorderItem, WorkorderItemAdmin)
    

#class ItemCategoryAdmin(admin.ModelAdmin):
#    fields = ['workorder', 'description', 'category', 'internal_company']


