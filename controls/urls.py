from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    #home,
    add_category,
    add_subcategory,
)

app_name='controls'

urlpatterns = [
    #path('', home, name='home'),
    path('add_category/', add_category, name='add_category'),
    path('add_subcategory/', add_subcategory, name='add_subcategory'),
        
]