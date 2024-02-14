from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    create_base,
    overview,
    workorder_list,
    edit_workorder,
    workorder_info,
    history_overview,
    workorder_item_list,
    add_item,
    edit_modal_item,
    edit_print_item,
    remove_workorder_item,
    copy_workorder_item,
    copy_workorder,
    subcategory,
    tax,
    notes,
    workorder_notes,
    edit_design_item,
    edit_orderout_item,
    edit_set_price_item,
    quote_list,
    # removed,
)

app_name='workorders'

urlpatterns = [
    path('', create_base, name='createbase'),
    path('add/<int:parent_id>/', add_item, name='add_item'),
    path('items/<int:pk>/edit/<int:cat>', edit_modal_item, name='edit_modal_item'),
    path('design/<int:pk>/edit/<int:cat>', edit_design_item, name='edit_design_item'),
    path('orderout/<int:pk>/edit/<int:cat>', edit_orderout_item, name='edit_orderout_item'),
    path('setprice/<int:pk>/edit/<int:cat>', edit_set_price_item, name='edit_set_price_item'),
    #path('items/<int:pk>/edit/<int:cat>', edit_print_item, name='edit_print_item'),
    path('items/<int:pk>/remove/', remove_workorder_item, name='remove_item'),
    path('items/copy_workorder/<int:id>', copy_workorder, name='copy_workorder'),
    path('items/<int:pk>/copy/', copy_workorder_item, name='copy_workorder_item'),
    path('items/<int:pk>/copy/<str:workorder>', copy_workorder_item, name='copy_workorder_item'),
    path("item/<int:id>/", workorder_item_list, name='workorder_item_list'),
    path("createbase/", create_base, name='createbase'), #Create base details of new workorder
    path("workorders/", workorder_list, name='workorder_list'),
    path("quotes/", quote_list, name='quote_list'),
    path("workorders/<int:id>", overview, name='overview'),
    path("workorders/<int:id>", history_overview, name='history_overview'),
    path("edit_workorder", edit_workorder, name='edit_workorder'),
    path("workorder_info/", workorder_info, name='workorder_info'),
    path("workorder_info/<int:workorder>/", workorder_info, name='workorder_info'),
    path('categories/', subcategory, name='subcategory'),
    path('tax/<str:tax>/<int:id>/', tax, name='tax'),
    path('notes/<int:pk>/', notes, name='notes'),
    path('notes/', notes, name='notes'),
    path('workordernotes/<int:pk>/', workorder_notes, name='workorder_notes'),
    # path('removed/', removed, name='removed')
    

]