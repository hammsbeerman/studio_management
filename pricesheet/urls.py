from django.urls import path

from .views import (
    envelope,
)

app_name='pricesheet'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('envelope/<int:pk>/edit/<int:cat>', views.envelope, name='envelope')
]