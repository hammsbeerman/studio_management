from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    list
)

app_name='inventory'

urlpatterns = [
    path('', list, name='list'),
        

]