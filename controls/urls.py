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
    workorder_ship
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
    #path('setprice_list/', setprice_list, name='setprice_list'),
]