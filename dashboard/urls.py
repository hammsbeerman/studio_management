from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    dashboard,
    dashboard2,
    assigned_item_list, 
    design_item_list, 
    selected_item_list,
    group_item_list,
    stale_item_list
)

app_name='dashboard'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('2/', dashboard2, name='dashboard2'),
    path('assigned_item_list/', assigned_item_list, name='assigned_item_list'),
    path('design_item_list/', design_item_list, name='design_item_list'),
    path('selected_item_list/', selected_item_list, name='selected_item_list'),
    path('group_item_list/', group_item_list, name='group_item_list'),
    path('stale_item_list/', stale_item_list, name='stale_item_list'),
]