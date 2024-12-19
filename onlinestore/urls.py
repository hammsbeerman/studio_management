from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    online_store_main,
    store_items,
    store_item_detail,
    edit_store_item
)

app_name='onlinestore'

urlpatterns = [
    path('', online_store_main, name='online_store'),
    path('store_items', store_items, name='store_items'),
    path('store_item_detail', store_item_detail, name='store_item_detail'),
    path('edit_store_item', edit_store_item, name='edit_store_item'),
]