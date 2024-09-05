from django.contrib import admin
from django.urls import path
#from rest_framework import routers
#from . import views


from .views import (
    vendor_list,
    add_vendor,
    vendor_detail,
    #add_inventory_item,
    edit_vendor,
    #Below this is solely for testing API data
    inventory_list,
    # InventoryCreate,
    # InventoryPRUD,
    # InventoryListAPIView,
    # InventoryDetailAPIView,
    # InventoryViewSet,
    item_variations,
    item_variation_details,
    #item_detail_select,
    item_details,
)

app_name='inventory'

urlpatterns = [
    path('vendors/<str:vendor>/', vendor_list, name='vendor_list'),
    path('vendors/', vendor_list, name='vendor_list'),
    path('add_vendor/', add_vendor, name='add_vendor'),
    path('edit_vendor/<int:id>/', edit_vendor, name='edit_vendor'),
    path('detail/<int:id>/', vendor_detail, name='vendor_detail'),
    #path('add_inventory_item/', add_inventory_item, name='add_inventory_item'),
    #Below this is solely for testing API data
    path('inventory_list/', inventory_list, name='inventory_list'),
    path('item_variations/', item_variations, name='item_variations'),
    path('item_variation_details/<int:id>/', item_variation_details, name='item_variation_details'),
    path('item_details/<int:id>/', item_details, name='item_details'),
    #path('item_detail_select/', item_detail_select, name='item_detail_select'),
    # path('inventory_create/', InventoryCreate.as_view(), name='inventory_create'),
    # path('inventory_prud/<int:pk>', InventoryPRUD.as_view(), name='inventory_prud'),
    # path('inventory_listapi/', InventoryListAPIView.as_view(), name='inventory_listapi'),
    # path('inventory_detailapi/<int:pk>', InventoryDetailAPIView.as_view(), name='inventory_detailapi'),
    #path('inventory_viewset/', InventoryViewSet.as_view(), name='inventory_viewset'),
]