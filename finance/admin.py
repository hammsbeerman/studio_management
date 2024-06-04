from django.contrib import admin

from .models import Payments, Araging, AccountsPayable, WorkorderPayment

admin.site.register(Payments)

admin.site.register(Araging)

admin.site.register(AccountsPayable)


class WorkorderPaymentAdmin(admin.ModelAdmin):
    list_display = ('workorder', 'payment', 'payment_amount', 'date')

admin.site.register(WorkorderPayment, WorkorderPaymentAdmin)