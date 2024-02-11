from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    home,
)

app_name='controls'

urlpatterns = [
    path('', home, name='home'),
        
]