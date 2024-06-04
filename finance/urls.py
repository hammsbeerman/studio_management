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
    finance_main,
    add_bill_payable,
    view_bills_payable,
    add_daily_sale,
    view_daily_sales,
    ar_aging,
    complete_not_billed,
    apply_other,
    krueger_ar,
    lk_ar,
    all_printleader,
    all_lk,
    open_invoices,
    open_invoices_recieve_payment,
    payment_history,
    remove_payment,
    all_open_printleader,
)

app_name='finance'

urlpatterns = [
    path('', finance_main, name='finance'),
    path('ap/bill_list/', bill_list, name='bill_list'),
    path('ar/dashboard/', ar_dashboard, name='ar_dashboard'),
    path('ar/dashboard/open_workorders/', open_workorders, name='open_workorders'),
    path('ar/dashboard/closed_workorders/<int:cust>/', closed_workorders, name='closed_workorders'),
    path('ar/recieve_payment/', recieve_payment, name='recieve_payment'),
    path('ar/unrecieve_payment/', unrecieve_payment, name='unrecieve_payment'),
    path('ar/recieve_payment/payment_detail/', payment_detail, name='payment_detail'),
    path('ar/recieve_payment/apply_payment/', apply_payment, name='apply_payment'),
    path('ar/recieve_payment/unapply_payment/', unapply_payment, name='unapply_payment'),
    path('bill_payable/', add_bill_payable, name='add_bill_payable'),
    path('view_bills/', view_bills_payable, name='view_bills_payable'),
    path('daily_sale/', add_daily_sale, name='add_daily_sale'),
    path('view_sales/', view_daily_sales, name='view_daily_sales'),
    path('ar_aging/', ar_aging, name='ar_aging'),
    path('complete_not_billed/', complete_not_billed, name='complete_not_billed'),
    path('apply_other/<int:cust>/', apply_other, name='apply_other'),
    path('krueger_ar/', krueger_ar, name='krueger_ar'),
    path('lk_ar/', lk_ar, name='lk_ar'),
    path('all_printleader/', all_printleader, name='all_printleader'),
    path('all_open_printleader/', all_open_printleader, name='all_open_printleader'),
    path('all_lk/', all_lk, name='all_lk'),
    path('open_invoices/<int:pk>/<int:msg>/', open_invoices, name='open_invoices'),
    path('open_invoices/<int:pk>/', open_invoices, name='open_invoices'),
    path('open_invoices_recieve_payment/<int:pk>/<int:msg>/', open_invoices_recieve_payment, name='open_invoices_recieve_payment'),
    path('open_invoices_recieve_payment/<int:pk>/', open_invoices_recieve_payment, name='open_invoices_recieve_payment'),
    path('ar/recieve_payment/payment_history/', payment_history, name='payment_history'),
    path('ar/remove_payment/<int:pk>/', remove_payment, name='remove_payment'),
    path('ar/remove_payment/', remove_payment, name='remove_payment'),

    #path('open_invoices/', open_invoices, name='open_invoices'),

    
        

]