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
    
    
    #path("customer_notes/", customer_notes, name='customer_notes'),
]