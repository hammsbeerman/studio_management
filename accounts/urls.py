from django.contrib import admin
from django.urls import path
from . import views

from .views import (
    login_view,
    logout_view,
    #register_view,
    update_password,
)

app_name='accounts'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('register/', views.register_view, name='register'),
    path("password/update/", views.update_password, name="update_password"),
    #path('update_password', update_password, name='update_password'),
]