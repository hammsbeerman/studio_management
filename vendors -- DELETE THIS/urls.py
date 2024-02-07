from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    vendor_list,
)

app_name='vendors'

urlpatterns = [
    path('', vendor_list, name='vendor_list'),
        

]