from django.contrib import admin

from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "primary_company", "date_created")
    search_fields = ("user__username", "email", "phone", "name")
    list_filter = ("primary_company",)
