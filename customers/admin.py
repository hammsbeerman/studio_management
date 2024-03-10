from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

# Register your models here.
from .models import Customer, Contact

class CustomerContactInline(admin.StackedInline):
    model = Contact
    extra = 0
    readonly_fields = ['created', 'updated']

class CustomerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [CustomerContactInline]
    readonly_fields = ['created', 'updated']
    fields = ['company_name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'logo', 'notes', 'website', 'po_number', 'tax_exempt', 'updated', 'credit']


admin.site.register(Customer, CustomerAdmin)

admin.site.register(Contact)

#admin.site.register(CustomerContact)