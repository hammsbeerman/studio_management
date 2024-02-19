from django.urls import path

from .views import (
    render_pdf_view,
    CustomerListView, 
    customer_render_pdf_view,
    show_workorder_items,
    pdf_report_create,
    export_pdf,
    management,
    export_batch_statement_pdf,
    lineitem_pdf
)

app_name='pdf'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('', CustomerListView.as_view(), name='customer-list-view'),
    path('test/', render_pdf_view, name='test-view'),
    path('<pk>/', customer_render_pdf_view, name='customer-pdf-view'),
    path('showitems/', show_workorder_items, name='showitems'),
    path('pdfcreate/', pdf_report_create, name='create_pdf'),
    path('export_pdf/<int:id>/', export_pdf, name='export_pdf'),
    path('management/', management, name='management'),
    path('lineitem_pdf/<int:id>/', lineitem_pdf, name='lineitem_pdf'),
    path('export_batch_statement_pdf/', export_batch_statement_pdf, name='export_batch_statement_pdf'),
]