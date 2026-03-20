from django.urls import path

from .views import add_note, archive_search, customer_panel, edit_overlay, link_asset, picker, workorder_panel

app_name = "archive_overlay"

urlpatterns = [
    path("search/", archive_search, name="search"),
    path("picker/", picker, name="picker"),
    path("link/", link_asset, name="link"),
    path("overlay/<int:pk>/edit/", edit_overlay, name="edit_overlay"),
    path("overlay/<int:pk>/note/", add_note, name="add_note"),
    path("customer/<int:customer_id>/panel/", customer_panel, name="customer_panel"),
    path("workorder/<int:workorder_id>/panel/", workorder_panel, name="workorder_panel"),
]
