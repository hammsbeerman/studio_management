from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    create_base,
    test_base,
    overview,
    workorder_list,
    edit_workorder,
    workorder_info,
    history_overview,
    workorder_item_list,
    add_item,
    edit_design_item,
    edit_print_item,
    remove_workorder_item,
)

app_name='workorders'

urlpatterns = [
    path('', create_base, name='createbase'),
    path('add/<int:parent_id>/', add_item, name='add_item'),
    path('items/<int:pk>/edit/<int:cat>', edit_design_item, name='edit_design_item'),
    path('items/<int:pk>/edit/<int:cat>', edit_print_item, name='edit_print_item'),
    path('items/<int:pk>/remove/', remove_workorder_item, name='remove_item'),
    path("item/<int:id>/", workorder_item_list, name='workorder_item_list'),
    path("createbase/", create_base, name='createbase'), #Create base details of new workorder
    path("testbase/", test_base, name='testbase'), #Create base details of new workorder
    path("workorders/", workorder_list, name='workorder_list'),
    path("workorders/<int:id>", overview, name='overview'),
    path("workorders/<int:id>", history_overview, name='history_overview'),
    path("edit_workorder", edit_workorder, name='edit_workorder'),
    path("workorder_info/", workorder_info, name='workorder_info'),
    

    

]