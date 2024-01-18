from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    create_base,
    test_base,
    customer_info,
    contacts,
    new_customer,
    customers,
    new_contact,
    items,
    workorder_list,
    edit_customer,
    cust_info,
)

app_name='workorders'

urlpatterns = [
    path('', create_base, name='createbase'),
    path("createbase/", create_base, name='createbase'), #Create base details of new workorder
    path("testbase/", test_base, name='testbase'), #Create base details of new workorder
    path("customer_info/", customer_info, name='customer_info'), #Create base details of new workorder
    path("contacts/", contacts, name='contacts'),
    path("new_customer/", new_customer, name='new_customer'),
    path("customers/", customers, name='customer_list'),
    path("new_contact/", new_contact, name='new_contact'),
    path("edit_customer/", edit_customer, name='edit_customer'),
    path("items/", workorder_list, name='workorder_list'),
    path("items/<int:id>", items, name='items'),
    path("cust_info/", cust_info, name='cust_info')
    

]