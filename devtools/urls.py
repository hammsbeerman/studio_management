from django.urls import path
from .views import changed_templates_dashboard, preview_template

app_name='devtools'

urlpatterns = [
    path("changed-templates/", changed_templates_dashboard, name="changed_templates"),
    path("preview-template/", preview_template, name="preview_template"),
]
