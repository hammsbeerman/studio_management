from django.contrib import admin
from django.urls import path
#from rest_framework import routers
#from . import views


from .views import (
    vendor_list,
    add_vendor,
    vendor_detail,
    add_inventory_item,
    edit_vendor,
    #Below this is solely for testing API data
    inventory_list,
    # InventoryCreate,
    # InventoryPRUD,
    # InventoryListAPIView,
    # InventoryDetailAPIView,
    # InventoryViewSet,
)

app_name='inventory'

urlpatterns = [
    path('vendors/<str:vendor>/', vendor_list, name='vendor_list'),
    path('vendors/', vendor_list, name='vendor_list'),
    path('add_vendor/', add_vendor, name='add_vendor'),
    path('edit_vendor/<int:id>/', edit_vendor, name='edit_vendor'),
    path('detail/<int:id>/', vendor_detail, name='vendor_detail'),
    path('add_inventory_item/', add_inventory_item, name='add_inventory_item'),
    #Below this is solely for testing API data
    path('inventory_list/', inventory_list, name='inventory_list'),
    # path('inventory_create/', InventoryCreate.as_view(), name='inventory_create'),
    # path('inventory_prud/<int:pk>', InventoryPRUD.as_view(), name='inventory_prud'),
    # path('inventory_listapi/', InventoryListAPIView.as_view(), name='inventory_listapi'),
    # path('inventory_detailapi/<int:pk>', InventoryDetailAPIView.as_view(), name='inventory_detailapi'),
    #path('inventory_viewset/', InventoryViewSet.as_view(), name='inventory_viewset'),
]