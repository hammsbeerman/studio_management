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
    edit_wideformat_item,
    wideformat_template,
)

app_name='pricesheet'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('envelope/<int:pk>/edit/<int:cat>', envelope, name='envelope'),
    path('template/<int:id>/', template, name='template'),
    path('wideformat_template/<int:id>/', wideformat_template, name='wideformat_template'),
    path('templates/', template_list, name='template_list'),
    path('templates/<int:id>', template_list, name='template_listing'),
    path('copy_template/', copy_template, name='copy_template'),
    path('add_template/', add_template, name='add_template'),
    path('subcategories/', subcategory, name='subcategory'),
    path('removetemplate/', remove_template, name='remove_template'),
    path('edititem/<int:id>/<int:pk>/<int:cat>/', edititem, name='edititem'),
    path('edit_wideformat_item/<int:pk>/<int:cat>/', edit_wideformat_item, name='edit_wideformat_item'),
    path('setprices/', setprices, name='setprices'),
    path('setqty/', setqty, name='setqty'),
]