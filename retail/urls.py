from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    retail_home,
    subcat,
    parent,
    add_vendor,
    vendor_list,
    vendor_detail,
    invoice_list,
    invoice_detail,
    add_invoice,
    add_invoice_item,
    #invoice_item_remainder,
    add_item_to_vendor,
    add_inventory_item,
    vendor_item_remainder,
    retail_inventory_list,
    edit_invoice_item
)

app_name='retail'

urlpatterns = [
    #path('', home, name='home'),
    path('', retail_home, name='retail_home'),
    path('add_vendor/', add_vendor, name='add_vendor'),
    path('add_invoice/', add_invoice, name='add_invoice'),
    #path('add_invoice_item/', add_invoice_item, name='add_invoice_item'),
    path('add_invoice_item/<int:invoice>/<int:vendor>', add_invoice_item, name='add_invoice_item'),
    path('add_invoice_item/<int:invoice>/', add_invoice_item, name='add_invoice_item'),
    path('edit_invoice_item/<int:invoice>/<int:id>', edit_invoice_item, name='edit_invoice_item'),
    path('edit_invoice_item/<int:id>/', edit_invoice_item, name='edit_invoice_item'),
    #path('add_invoice_item/', add_invoice_item, name='add_invoice_item'),
    #path('invoice_item_remainder/<int:vendor>/<int:invoice>', invoice_item_remainder, name='invoice_item_remainder'),
    path('vendor_list/', vendor_list, name='vendor_list'),
    path('invoice_list/', invoice_list, name='invoice_list'),
    path('vendor_detail/<int:id>/', vendor_detail, name='vendor_detail'),
    path('invoice_detail/', invoice_detail, name='invoice_detail'),
    path('invoice_detail/<int:id>/', invoice_detail, name='invoice_detail'),
    path('subcat/<int:cat>/', subcat, name='subcat'),
    path('parent/<int:cat>/', parent, name='parent'),
    path('add_item_to_vendor/<int:vendor>/<int:invoice>', add_item_to_vendor, name='add_item_to_vendor'),
    path('add_item_to_vendor/', add_item_to_vendor, name='add_item_to_vendor'),
    path('add_inventory_item/<int:vendor>/<int:invoice>', add_inventory_item, name='add_inventory_item'),
    path('add_inventory_item/', add_inventory_item, name='add_inventory_item'),
    path('vendor_item_remainder/<int:vendor>/<int:invoice>', vendor_item_remainder, name='vendor_item_remainder'),
    path('retail_inventory_list/', retail_inventory_list, name='retail_inventory_list'),



]