from django.contrib import admin
from django.conf import settings
from django.http import HttpResponseBadRequest
from .models import DevTool

@admin.register(DevTool)
class DevToolAdmin(admin.ModelAdmin):
    change_list_template = "devtools/change_list.html"

    def has_add_permission(self, request):  # no add/edit/delete
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if not settings.DEBUG:
            return HttpResponseBadRequest("Dev tools are available only in DEBUG.")
        extra_context = extra_context or {}
        from django.urls import reverse
        extra_context.update({
            "dashboard_url": reverse("devtools:changed_templates"),
            "default_base": "original/main",
        })
        return super().changelist_view(request, extra_context=extra_context)