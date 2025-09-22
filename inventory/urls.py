from django.urls import path
from .views import (
    VendorListView, add_vendor, edit_vendor, vendor_detail,
    inventory_list, item_variations, item_variation_details, item_details,
)

app_name = "inventory"

urlpatterns = [
    # ---- Specific vendor routes (new canonical) ----
    
    path("vendors/add/", add_vendor, name="add_vendor"),
    path("vendors/<int:id>/edit/", edit_vendor, name="edit_vendor"),
    path("vendors/<int:id>/", vendor_detail, name="vendor_detail"),

    # ---- Back-compat aliases used by older templates/tests ----
    path("edit_vendor/<int:id>/", edit_vendor, name="edit_vendor_legacy"),
    path("detail/<int:id>/", vendor_detail, name="vendor_detail_legacy"),
    path("vendors/detail/<int:id>/", vendor_detail, name="vendor_detail_vendorprefix_legacy"),

    # ---- List views (place AFTER the specific routes) ----
    path("vendors/<str:vendor>/", VendorListView.as_view(), name="vendor_list"),
    path("vendors/", VendorListView.as_view(), name="vendor_list"),

    # ---- Items / misc ----
    path("inventory_list/", inventory_list, name="inventory_list"),
    path("item_variations/", item_variations, name="item_variations"),
    path("item_variation_details/<int:id>/", item_variation_details, name="item_variation_details"),
    path("item_details/<int:id>/", item_details, name="item_details"),
    path("item_details/", item_details, name="item_details"),
]