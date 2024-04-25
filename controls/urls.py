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
    #path('setprice_list/', setprice_list, name='setprice_list'),
]