from django.contrib import admin

from .models import Payments, Araging, AccountsPayable, WorkorderPayment, InvoiceItem#, AllInvoiceItem

admin.site.register(Payments)

admin.site.register(Araging)

admin.site.register(AccountsPayable)

#admin.site.register(AllInvoiceItem)

class InvoiceItemAdmin(admin.ModelAdmin):
    readonly_fields=('invoice_unit',)

admin.site.register(InvoiceItem, InvoiceItemAdmin)
    

class WorkorderPaymentAdmin(admin.ModelAdmin):
    list_display = ('workorder', 'payment', 'payment_amount', 'date')

admin.site.register(WorkorderPayment, WorkorderPaymentAdmin)