from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    online_store_main,
    store_items
)

app_name='onlinestore'

urlpatterns = [
    path('', online_store_main, name='online_store'),
    path('store_items', store_items, name='store_items'),
]