from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    bill_list,
    ar_dashboard,
    open_workorders,
    closed_workorders,
    recieve_payment,
    payment_detail,
    apply_payment,
    unapply_payment,
    unrecieve_payment,
)

app_name='finance'

urlpatterns = [
    path('ap/bill_list/', bill_list, name='bill_list'),
    path('ar/dashboard/', ar_dashboard, name='ar_dashboard'),
    path('ar/dashboard/open_workorders/', open_workorders, name='open_workorders'),
    path('ar/dashboard/closed_workorders/<int:cust>/', closed_workorders, name='closed_workorders'),
    path('ar/recieve_payment/', recieve_payment, name='recieve_payment'),
    path('ar/unrecieve_payment/', unrecieve_payment, name='unrecieve_payment'),
    path('ar/recieve_payment/payment_detail/', payment_detail, name='payment_detail'),
    path('ar/recieve_payment/apply_payment/', apply_payment, name='apply_payment'),
    path('ar/recieve_payment/unapply_payment/', unapply_payment, name='unapply_payment'),
        

]