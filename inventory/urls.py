from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    vendor_list,
    add_vendor,
    detail,
    add_inventory_item
)

app_name='inventory'

urlpatterns = [
    path('vendors/', vendor_list, name='vendor_list'),
    path('add_vendor/', add_vendor, name='add_vendor'),
    path('detail/<int:id>/', detail, name='detail'),
    path('add_inventory_item/', add_inventory_item, name='add_inventory_item'),
        

]