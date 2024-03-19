from django.urls import path

from .views import (
    newjob,
    paperprice,
    wideformat_paperprice,
    wideformat_maskprice,
    wideformat_laminateprice,
    wideformat_substrateprice,
    #remove_workorder_item,
)

app_name='krueger'

from . import views

urlpatterns = [
    path('', views.newjob, name='krueger-print'),
    #path('papers/', views.paper, name='paper'),
    path('wideformat_paperprice/', views.wideformat_paperprice, name='wideformat_paperprice'),
    path('wideformat_maskprice/', views.wideformat_maskprice, name='wideformat_maskprice'),
    path('wideformat_laminateprice/', views.wideformat_laminateprice, name='wideformat_laminateprice'),
    path('wideformat_substrateprice/', views.wideformat_substrateprice, name='wideformat_substrateprice'),
    path('paperprice/', views.paperprice, name='paperprice'),
    #path('delete_customer/<int:pk>', views.papersizes, name='delete_customer'),
    path("print/<int:id>/<int:pk>/", views.newjob, name='bigform'),
    #path("remove/", views.remove_workorder_item, name='remove_item')
]