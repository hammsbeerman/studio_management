from django.urls import path, include
from .views import (
    VendorListView, VendorDetailView, edit_vendor, vendor_detail,
    inventory_list, item_variations, item_variation_details, item_details, vendor_add,
    merge_items, undo_merge, view_variations, view_variation_details
)

app_name = "inventory"

urlpatterns = [
    # Vendors
    path("vendors/add/", vendor_add, name="add_vendor"),
    path("vendors/", VendorListView.as_view(), name="vendor_list"),
    path("vendors/<int:id>/", VendorDetailView.as_view(), name="vendor_detail"),
    path("vendors/<int:id>/edit/", edit_vendor, name="edit_vendor"),
    path("vendors/<str:vendor>/", VendorListView.as_view(), name="vendor_list"),
    
    #path("vendors/add/", add_vendor, name="add_vendor"),
    
    # path("vendors/<int:id>/edit/", edit_vendor, name="edit_vendor"),
    # path("vendors/<int:id>/", vendor_detail, name="vendor_detail"),

    

    # Item variations & details (for your tests)

    path("items/", item_details, name="item_details"),
    path("items/<int:id>/", item_details, name="item_details_id"),
    path("items/details/", item_details, name="item_details"),
    path("items/details/<int:id>/", item_details, name="item_details_id"),
    path("items/view_variations/", view_variations, name="item_variations"),
    path("items/view_variation_details/<int:id>/", view_variation_details, name="item_variation_details"),
    path("items/variations/", item_variations),
    path("items/variations/<int:id>/", item_variation_details),
    
    path("merge/", merge_items, name="merge_items"),
    path("merge/undo/<int:log_id>/", undo_merge, name="undo_merge"),
    

    # Misc inventory
    path("inventory_list/", inventory_list, name="inventory_list"),

    path("api/", include("inventory.urls_api")),
]
