from django.contrib import admin
from .models import Numbering, FixedCost, Category, SubCategory, DesignType, Measurement, SetPriceCategory, SetPriceItemPrice, InventoryCategory, JobStatus, UserGroup, PaymentType, RetailInventoryCategory, RetailInventorySubCategory, GroupCategory
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.fields import Field
from import_export.widgets import DateWidget


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

admin.site.register(GroupCategory)




class RetailInventoryCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name',)

admin.site.register(RetailInventoryCategory, RetailInventoryCategoryAdmin)

class RetailInventorySubCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name',)

admin.site.register(RetailInventorySubCategory, RetailInventorySubCategoryAdmin)


