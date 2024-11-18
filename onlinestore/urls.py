from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    online_store_main,
    store_items,
    store_item_detail
)

app_name='onlinestore'

urlpatterns = [
    path('', online_store_main, name='online_store'),
    path('store_items', store_items, name='store_items'),
    path('store_item_detail', store_item_detail, name='store_item_detail'),
]