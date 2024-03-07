from django.contrib import admin

from .models import Numbering, FixedCost, Category, SubCategory, DesignType, Measurement, SetPriceItem, SetPriceItemPrice, InventoryCategory, JobStatus, UserGroup



class NumberingAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'value')

admin.site.register(Numbering, NumberingAdmin)

class CategorySubcategoryInline(admin.StackedInline):
    model = SubCategory
    extra = 0

class InventoryCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name',)

admin.site.register(InventoryCategory, InventoryCategoryAdmin)

class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategorySubcategoryInline]
    list_display = ('name', 'description', 'design_type', 'formname', 'modelname', 'modal', 'template', 'pricesheet_type')

admin.site.register(Category, CategoryAdmin)



class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description', 'template')

admin.site.register(SubCategory, SubCategoryAdmin)

#class FixedCostAdmin(admin.ModelAdmin):

admin.site.register(FixedCost)

admin.site.register(DesignType)

admin.site.register(Measurement)

admin.site.register(SetPriceItem)

admin.site.register(SetPriceItemPrice)

admin.site.register(JobStatus)

admin.site.register(UserGroup)
