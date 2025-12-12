from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    #customer_info,
    contacts,
    new_customer,
    customers,
    new_contact,
    edit_customer,
    cust_info,
    edit_contact,
    contact_info,
    change_contact,
    new_cust_contact,
    customer_list,
    customer_notes,
    #detail,
    dashboard,
    expanded_detail,
    details_contact_info,
    edit_shipto,
    new_shipto,
    change_shipto,
    customer_list,
    add_mailing_customer,
    edit_mailing_customer,
    delete_mailing_customer,
    customer_tab_open,
    customer_tab_quotes,
    customer_tab_completed,
    customer_tab_payments,
)

app_name='customers'

urlpatterns = [

    #path("customer_info/", customer_info, name='customer_info'), #Create base details of new workorder
    path("contacts/", contacts, name='contacts'),
    path("customers/", customers, name='customers'),
    path("customer_list/", customer_list, name='customer_list'),
    path("new_customer/", new_customer, name='new_customer'),
    path("new_contact/", new_contact, name='new_contact'),
    path("new_cust_contact/", new_cust_contact, name='new_cust_contact'),
    path("edit_customer/", edit_customer, name='edit_customer'),
    path("change_contact/", change_contact, name='change_contact'),
    path("cust_info/", cust_info, name='cust_info'),
    path("edit_contact/", edit_contact, name='edit_contact'),
    path("contact_info/", contact_info, name='contact_info'),
    path("details_contact_info/", details_contact_info, name='details_contact_info'),
    path("customer_notes/<int:pk>/", customer_notes, name='customer_notes'),
    #path("detail/<int:id>/", detail, name='detail'),
    path("dashboard/", dashboard, name='customer_dashboard'),
    path("dashboard/details/<int:id>/", expanded_detail, name='expanded_details'),
    path("dashboard/details/", expanded_detail, name='expanded_detail'),
    path("edit_shipto/", edit_shipto, name='edit_shipto'),
    path("new_shipto/", new_shipto, name='new_shipto'),
    path("change_shipto/", change_shipto, name='change_shipto'),
    path("customer_list/<str:customer>/", customer_list, name='customer_list'),
    path("customer_list/", customer_list, name='customer_list'),
    path("add_mailing_customer/", add_mailing_customer, name='add_mailing_customer'),
    path("edit_mailing_customer/<int:mailing>/", edit_mailing_customer, name='edit_mailing_customer'),
    path("delete_mailing_customer/<int:mailing>/", delete_mailing_customer, name='delete_mailing_customer'),
    path("customer/<int:customer_id>/tab/open/", customer_tab_open, name="customer_tab_open"),
    path("customer/<int:customer_id>/tab/quotes/", customer_tab_quotes, name="customer_tab_quotes"),
    path("customer/<int:customer_id>/tab/completed/", customer_tab_completed, name="customer_tab_completed"),
    path("customer/<int:customer_id>/tab/payments/", customer_tab_payments, name="customer_tab_payments"),

    
    
    #path("customer_notes/", customer_notes, name='customer_notes'),
]