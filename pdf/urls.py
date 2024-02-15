from django.urls import path

from .views import (
    render_pdf_view,
    CustomerListView, 
    customer_render_pdf_view
)

app_name='pdf'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('', CustomerListView.as_view(), name='customer-list-view'),
    path('test/', render_pdf_view, name='test-view'),
    path('<pk>/', customer_render_pdf_view, name='customer-pdf-view'),
]