from django.contrib import admin

from .models import Numbering, FixedCost, Category, SubCategory, DesignType, Measurement, SetPriceCategory, SetPriceItemPrice, InventoryCategory, JobStatus, UserGroup, PaymentType, RetailInventoryCategory, RetailInventorySubCategory



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

admin.site.register(SetPriceCategory)

admin.site.register(SetPriceItemPrice)

admin.site.register(JobStatus)

admin.site.register(UserGroup)

admin.site.register(PaymentType)




class RetailInventoryCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name',)

admin.site.register(RetailInventoryCategory, RetailInventoryCategoryAdmin)

class RetailInventorySubCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name',)

admin.site.register(RetailInventorySubCategory, RetailInventorySubCategoryAdmin)
