from django.urls import path

from .views import (
    newjob,
    paperprice,
    remove_workorder_item,
)

app_name='krueger'

from . import views

urlpatterns = [
    path('', views.newjob, name='krueger-print'),
    #path('papers/', views.paper, name='paper'),
    path('paperprice/', views.paperprice, name='paperprice'),
    #path('delete_customer/<int:pk>', views.papersizes, name='delete_customer'),
    path("print/<int:id>/<int:pk>/", views.newjob, name='bigform'),
    path("remove/", views.remove_workorder_item, name='remove_item')
]