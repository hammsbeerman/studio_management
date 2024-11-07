from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, Max, Count, Min, Sum, Subquery, Case, When, Value, DecimalField, OuterRef
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import logging
from .models import AccountsPayable, DailySales, Araging, Payments, WorkorderPayment
from .forms import AccountsPayableForm, DailySalesForm, AppliedElsewhereForm, PaymentForm
from retail.forms import RetailInventoryMasterForm
from finance.forms import AddInvoiceForm, AddInvoiceItemForm, EditInvoiceForm
from finance.models import InvoiceItem#, AllInvoiceItem
from customers.models import Customer
from workorders.models import Workorder
from controls.models import PaymentType, Measurement
from inventory.models import Vendor, InventoryMaster, VendorItemDetail, InventoryQtyVariations, InventoryPricingGroup, Inventory
from inventory.forms import InventoryMasterForm, VendorItemDetailForm
from onlinestore.models import StoreItemDetails

def ar_aging():
    # update_ar = request.GET.get('up')
    # print('update')
    # print(update_ar)
    # #customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
    today = timezone.now()
    customers = Customer.objects.all()
    ar = Araging.objects.all()
    workorders = Workorder.objects.filter().exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1)
    for x in workorders:
        #print(x.id)
        if not x.date_billed:
            x.date_billed = today
        age = x.date_billed - today
        age = abs((age).days)
        print(age)
        Workorder.objects.filter(pk=x.pk).update(aging = age)
    total_balance = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    for x in customers:
        # try:
        #     #Get the Araging customer and check to see if aging has been updated today
        #     modified = Araging.objects.get(customer=x.id)
        #     print(x.company_name)
        #     day = today.strftime('%Y-%m-%d')
        #     day = str(day)
        #     date = str(modified.date)
        #     print(day)
        #     print(date)
        #     if day == date:
        #         #Don't update, as its been done today
        #         print('today')
        #         update = 0
        #         if update_ar == '1':
        #             print('update')
        #             update = 1
        #     else:
        #         update = 1
        # except:
        #     update = 1
        #Update the Araging that needs to be done
        # if update == 1:
        if Workorder.objects.filter(customer_id = x.id).exists():
            current = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
            try:
                current = list(current.values())[0]
            except:
                current = 0
            thirty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
            try: 
                thirty = list(thirty.values())[0]
            except:
                thirty = 0
            sixty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
            try:
                sixty = list(sixty.values())[0]
            except:
                sixty = 0
            ninety = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
            try:
                ninety = list(ninety.values())[0]
            except:
                ninety = 0
            onetwenty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
            try:
                onetwenty = list(onetwenty.values())[0]
            except:
                onetwenty = 0
            total = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
            try:
                total = list(total.values())[0]
            except:
                total = 0
            try: 
                obj = Araging.objects.get(customer_id=x.id)
                Araging.objects.filter(customer_id=x.id).update(hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
            except:
                obj = Araging(customer_id=x.id,hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
                obj.save()
    ar = Araging.objects.all().order_by('hr_customer')
    #total_current = Araging.objects.filter().aggregate(Sum('current'))
    total_current = ar.filter().aggregate(Sum('current'))
    # total_thirty = ar.filter().aggregate(Sum('thirty'))
    # total_sixty = ar.filter().aggregate(Sum('sixty'))
    # total_ninety = ar.filter().aggregate(Sum('ninety'))
    # total_onetwenty = ar.filter().aggregate(Sum('onetwenty'))
    print(total_current)
    
    # #print(ar)
    # context = {
    #     'total_current':total_current,
    #     'total_thirty':total_thirty,
    #     'total_sixty':total_sixty,
    #     'total_ninety':total_ninety,
    #     'total_onetwenty':total_onetwenty,
    #     'total_balance':total_balance,
    #     'ar': ar
    # }
    # return render(request, 'finance/reports/ar_aging.html', context)