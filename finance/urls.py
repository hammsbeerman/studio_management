from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    bill_list
)

app_name='finance'

urlpatterns = [
    path('', bill_list, name='bill_list'),
        

]