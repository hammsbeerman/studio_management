from django.contrib import admin

from .models import Workorder, Numbering, Category, WorkorderItem, DesignType, SubCategory #ItemCategory, 


class WorkorderAdmin(admin.ModelAdmin):
    fields = ['customer', 'workorder', 'internal_company', 'description', 'deadline', 'budget', 'quoted_price', 'original_order', 'billed', 'notes']
    list_display = ('customer', 'workorder', 'internal_company', 'description', 'deadline', 'budget', 'quoted_price', 'original_order', 'billed')

admin.site.register(Workorder, WorkorderAdmin)


class NumberingAdmin(admin.ModelAdmin):
    readonly_fields=('value',)
    list_display = ('name', 'value')

admin.site.register(Numbering, NumberingAdmin)

# class ItemCategoryAdmin(admin.ModelAdmin):
#    #extra = 0
#    # readonly_fields = ['created', 'updated']
#     fields = ['workorder', 'description', 'category', 'internal_company']
#     ordering = ('-workorder',)

# admin.site.register(ItemCategory, ItemCategoryAdmin)


class WorkorderItemAdmin(admin.ModelAdmin):
    list_display = ('workorder', 'item_category', 'design_type', 'description', 'quantity', 'unit_price', 'total_price')

admin.site.register(WorkorderItem, WorkorderItemAdmin)
    

#class ItemCategoryAdmin(admin.ModelAdmin):
#    fields = ['workorder', 'description', 'category', 'internal_company']

class CategorySubcategoryInline(admin.StackedInline):
    model = SubCategory
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategorySubcategoryInline]
    list_display = ('name', 'description', 'design_type', 'formname', 'modal')

admin.site.register(Category, CategoryAdmin)



class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')

admin.site.register(SubCategory, SubCategoryAdmin)





admin.site.register(DesignType)


