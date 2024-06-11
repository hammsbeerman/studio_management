from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    retail_home,
    subcat,
    parent,
)

app_name='retail'

urlpatterns = [
    #path('', home, name='home'),
    path('retail/', retail_home, name='retail_home'),
    path('subcat/<int:cat>/', subcat, name='subcat'),
    path('parent/<int:cat>/', parent, name='parent'),

]