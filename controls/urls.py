from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    #home,
    add_category,
    add_subcategory,
    add_setprice_item,
    add_setprice_category,
    utilities,
    mark_all_verified,
    mark_all_invoiced,
    missing_workorders,
    update_complete_date,
    special_tools,
    customer_shipto,
    workorder_ship,
    cust_history,
    cust_address,
    cust_wo_address,
    create_inventory_from_inventory,
    add_primary_vendor,
    add_units_per_base_unit,
    view_price_groups,
    view_price_group_detail,
    add_price_group,
    add_price_group_item,
    add_primary_baseunit,
    add_item_variation,
    #setprice_list,
)

app_name='controls'

urlpatterns = [
    #path('', home, name='home'),
    path('add_category/', add_category, name='add_category'),
    path('add_subcategory/', add_subcategory, name='add_subcategory'),
    path('add_setprice_category/', add_setprice_category, name='add_setprice_category'),
    path('add_setprice_item/', add_setprice_item, name='add_setprice_item'),
    path('utilities/', utilities, name='utilities'),
    path('mark_verified/', mark_all_verified, name='mark_all_verified'),
    path('mark_invoiced/', mark_all_invoiced, name='mark_all_invoiced'),
    path('missing_workorders/', missing_workorders, name='missing_workorders'),
    path('update_complete_date/', update_complete_date, name='update_complete_date'),
    path('special_tools/', special_tools, name='special_tools'),
    path('customer_shipto/', customer_shipto, name='customer_shipto'),
    path('workorder_ship/', workorder_ship, name='workorder_ship'),
    path('cust_history/', cust_history, name='cust_history'),
    path('cust_address/', cust_address, name='cust_address'),
    path('cust_wo_address/', cust_wo_address, name='cust_wo_address'),
    path('create_inventory_from_inventory/', create_inventory_from_inventory, name='create_inventory_from_inventory'),
    path('add_primary_vendor/', add_primary_vendor, name='add_primary_vendor'),
    path('add_units_per_base_unit/', add_units_per_base_unit, name='add_units_per_base_unit'),
    path('view_price_groups/', view_price_groups, name='view_price_groups'),
    path('view_price_group_detail/<int:id>/', view_price_group_detail, name='view_price_group_detail'),
    path('add_price_group/', add_price_group, name='add_price_group'),
    path('add_price_group_item/', add_price_group_item, name='add_price_group_item'),
    path('add_primary_baseunit/', add_primary_baseunit, name='add_primary_baseunit'),
    path('add_item_variation/', add_item_variation, name='add_item_variation'),
    #path('setprice_list/', setprice_list, name='setprice_list'),
]