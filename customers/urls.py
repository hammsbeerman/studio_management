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
)

app_name='customers'

urlpatterns = [

    #path("customer_info/", customer_info, name='customer_info'), #Create base details of new workorder
    path("contacts/", contacts, name='contacts'),
    path("customers/", customers, name='customer_list'),
    path("new_customer/", new_customer, name='new_customer'),
    path("new_contact/", new_contact, name='new_contact'),
    path("new_cust_contact/", new_cust_contact, name='new_cust_contact'),
    path("edit_customer/", edit_customer, name='edit_customer'),
    path("change_contact/", change_contact, name='change_contact'),
    path("cust_info/", cust_info, name='cust_info'),
    path("edit_contact/", edit_contact, name='edit_contact'),
    path("contact_info/", contact_info, name='contact_info'),

]