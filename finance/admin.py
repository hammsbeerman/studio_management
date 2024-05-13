from django.contrib import admin

from .models import Payments, Araging, AccountsPayable

admin.site.register(Payments)

admin.site.register(Araging)

admin.site.register(AccountsPayable)