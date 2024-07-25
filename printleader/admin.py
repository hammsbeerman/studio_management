from django.contrib import admin
from .models import PrintleaderHistory, PrintleaderARINVODA, PrintleaderSOORDEDT, PrintleaderSORITL
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.fields import Field
from import_export.widgets import DateWidget

class PrintleaderHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['printleader_invoice', 'customer']
    list_display = ('customer', 'printleader_invoice')
    invoice_date = Field(attribute='invoice_date', column_name='invoice_date', widget=DateWidget('%m/%d/%Y'))
    #fields = ['name',]

admin.site.register(PrintleaderHistory, PrintleaderHistoryAdmin)

class PrintleaderARINVODAAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['InvoiceNum']
    list_display = ('InvoiceNum', 'Jobname')
    #invoice_date = Field(attribute='invoice_date', column_name='invoice_date', widget=DateWidget('%m/%d/%Y'))
    #fields = ['name',]

admin.site.register(PrintleaderARINVODA, PrintleaderARINVODAAdmin)

class PrintleaderSOORDEDTAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['OrderNum']
    list_display = ('OrderNum', 'Job_Category')
    #invoice_date = Field(attribute='invoice_date', column_name='invoice_date', widget=DateWidget('%m/%d/%Y'))
    #fields = ['name',]

admin.site.register(PrintleaderSOORDEDT, PrintleaderSOORDEDTAdmin)


class PrintleaderSORITLAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    #inlines = [InventoryVendorInline]
    readonly_fields = ['Invoice']
    list_display = ('Invoice', 'E_desc')
    #invoice_date = Field(attribute='invoice_date', column_name='invoice_date', widget=DateWidget('%m/%d/%Y'))
    #fields = ['name',]

admin.site.register(PrintleaderSORITL, PrintleaderSORITLAdmin)