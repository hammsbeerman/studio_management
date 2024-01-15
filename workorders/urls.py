from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    create_base,
)

app_name='workorders'

urlpatterns = [
    path('', create_base, name='createbase'),
    path("createbase/", create_base, name='createbase'), #Create base details of new workorder
]