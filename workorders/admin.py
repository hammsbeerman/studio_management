from django.contrib import admin

from .models import Workorder, Numbering#, ItemCategory, Category, WorkorderItem, DesignType


class WorkorderAdmin(admin.ModelAdmin):
    fields = ['customer', 'workorder', 'internal_company', 'description', 'deadline', 'budget', 'quoted_price', 'original_order']

class NumberingAdmin(admin.ModelAdmin):
    readonly_fields=('value',)


admin.site.register(Workorder, WorkorderAdmin)

admin.site.register(Numbering, NumberingAdmin)
