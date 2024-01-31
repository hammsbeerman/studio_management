from django.urls import path

from .views import (
    envelope,
    template,
    template_list,
    add_category,
    add_subcategory,
    add_template,
    subcategory,
)

app_name='pricesheet'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('envelope/<int:pk>/edit/<int:cat>', views.envelope, name='envelope'),
    path('template/<int:id>/', views.template, name='template'),
    path('templates/', views.template_list, name='template_list'),
    path('add_category/', views.add_category, name='add_category'),
    path('add_subcategory/', views.add_subcategory, name='add_subcategory'),
    path('add_template/', views.add_template, name='add_template'),
    path('categories/', subcategory, name='subcategory'),
]