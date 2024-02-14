from django.urls import path

from .views import (
    envelope,
    template,
    template_list,
    add_template,
    subcategory,
    edititem,
    copy_template,
    remove_template,
    setprices,
    setqty,
)

app_name='pricesheet'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('envelope/<int:pk>/edit/<int:cat>', envelope, name='envelope'),
    path('template/<int:id>/', template, name='template'),
    path('templates/', template_list, name='template_list'),
    path('templates/<int:id>', template_list, name='template_listing'),
    path('copy_template/', copy_template, name='copy_template'),
    path('add_template/', add_template, name='add_template'),
    path('subcategories/', subcategory, name='subcategory'),
    path('removetemplate/', remove_template, name='remove_template'),
    path('edititem/<int:id>/<int:pk>/<int:cat>/', edititem, name='edititem'),
    path('setprices/', setprices, name='setprices'),
    path('setqty/', setqty, name='setqty'),
]