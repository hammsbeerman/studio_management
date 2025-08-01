from django.urls import path

from .views import (
    invoice_pdf,
    lineitem_pdf,
    ticket_pdf,
    statement_pdf,
    statement_pdf_bulk,
    #

    ####### These aren't currently used
    render_pdf_view,
    CustomerListView, 
    customer_render_pdf_view,
    show_workorder_items,
    pdf_report_create,
    management,
    export_batch_statement_pdf,
    
)

app_name='pdf'

from . import views

urlpatterns = [
    #path('', views.newjob, name='krueger-print'),
    path('invoice_pdf/<int:id>/', invoice_pdf, name='invoice_pdf'),
    path('lineitem_pdf/<int:id>/', lineitem_pdf, name='lineitem_pdf'),
    path('statement_pdf/<int:id>/', statement_pdf, name='statement_pdf'),
    path('statement_pdf/', statement_pdf_bulk, name='statement_pdf_bulk'),
    path('ticket_pdf/<int:id>/', ticket_pdf, name='ticket_pdf'),
    ###### These aren't currently used
    path('', CustomerListView.as_view(), name='customer-list-view'),
    path('test/', render_pdf_view, name='test-view'),
    path('<pk>/', customer_render_pdf_view, name='customer-pdf-view'),
    path('showitems/', show_workorder_items, name='showitems'),
    path('pdfcreate/', pdf_report_create, name='create_pdf'),
    
    path('management/', management, name='management'),
    
    path('export_batch_statement_pdf/', export_batch_statement_pdf, name='export_batch_statement_pdf'),
]