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
from .models import AccountsPayable, DailySales, Araging, Payments, WorkorderPayment, Krueger_Araging
from .forms import AccountsPayableForm, DailySalesForm, AppliedElsewhereForm, PaymentForm, DateRangeForm
from retail.forms import RetailInventoryMasterForm
from finance.forms import AddInvoiceForm, AddInvoiceItemForm, EditInvoiceForm, BulkEditInvoiceForm
from finance.models import InvoiceItem#, AllInvoiceItem
from customers.models import Customer
from workorders.models import Workorder
from controls.models import PaymentType, Measurement
from inventory.models import Vendor, InventoryMaster, VendorItemDetail, InventoryQtyVariations, InventoryPricingGroup, Inventory
from inventory.forms import InventoryMasterForm, VendorItemDetailForm
from onlinestore.models import StoreItemDetails

logger = logging.getLogger(__file__)

@login_required
def finance_main(request):
    return render(request, 'finance/main.html')

@login_required
def bill_list(request):
    pass

@login_required
def ar_dashboard(request):
    #item_status = ''
    customers = Customer.objects.all()
    context = {
        'customers':customers,
    }
    return render(request, "finance/AR/ar_dashboard.html", context)

@login_required
def open_workorders(request):
    customers = Customer.objects.all()
    if request.method == "GET":
        test = request.GET.get('test')
        print(test)
        customer = request.GET.get('customers')
        try:
            selected_customer = Customer.objects.get(id=customer)
        except:
            return HttpResponse(status=204, headers={'HX-Trigger': 'Payment Recieved'})
        try:
            workorders = Workorder.objects.filter(customer_id = customer).exclude(billed=0).exclude(total_balance=0).exclude(paid_in_full=1).order_by("-workorder")
        except:
            workorders = 'No Workorders Available'
    print(workorders)
    context = {
        'customer':selected_customer,
        'customers':customers,
        'workorders':workorders,
    }
    return render(request, "finance/AR/partials/workorder_list.html", context)

@login_required
def closed_workorders(request, cust):
    customers = Customer.objects.all()
    if request.method == "GET":
        customer = cust
        print(customer)
        selected_customer = Customer.objects.get(id=customer)
        try:
            workorders = Workorder.objects.filter(customer_id = customer).exclude(paid_in_full=0).order_by("-workorder")
        except:
            workorders = 'No Workorders Available'
    print(workorders)
    context = {
        'customer':selected_customer,
        'customers':customers,
        'workorders':workorders,
    }
    return render(request, "finance/AR/partials/closed_workorder_list.html", context)

@login_required
def recieve_payment(request):
    paymenttype = PaymentType.objects.all()
    customers = Customer.objects.all().order_by('company_name')
    if request.method == "POST":
            modal = request.POST.get('modal')
            id_list = request.POST.getlist('payment')
            payment_total = 0
            for x in id_list:
                print('payment total')
                print(payment_total)
                t = Workorder.objects.get(pk=int(x))
                balance = t.open_balance
                payment_total = payment_total + balance
            amount = request.POST.get('amount')
            amount = Decimal(amount)
            if payment_total > amount:
                form = PaymentForm
                customer = request.POST.get('customer')
                # context = {
                #     'paymenttype':paymenttype,
                #     'customers':customers,
                #     'form': form,
                # }
                return redirect('finance:open_invoices_recieve_payment', pk=customer, msg=1)
            # for x in id_list:
            #     Workorder.objects.filter(pk=int(x)).update(paid_in_full=True)
            print('testing123')
            customer = request.POST.get('customer')
            print(customer)
            check = request.POST.get('check_number')
            giftcard = request.POST.get('giftcard_number')
            refund = request.POST.get('refunded_invoice_number')
            date = request.POST.get('date')
            #date = date.datetime('%Y-%m-%d')
            #date = datetime.strptime(date, '%Y/%m/%d').date()
            date = datetime.strptime(date, '%m/%d/%Y')
            print(date)
            form = PaymentForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.check_number = check
                print(obj.check_number)
                obj.giftcard_number = giftcard
                obj.refunded_invoice_number = refund
                obj.save()
                print('Payment ID')
                payment_id = obj.pk
                remainder = amount
                payment_date = date.date()
                print(date)
                print(amount)
                for x in id_list:
                    #Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, paid_in_full = full_payment, date_paid = date)
                    amount = Workorder.objects.get(pk=int(x))
                    #Most of this fiddlefuckery is to convert datetimes to date
                    date_billed = amount.date_billed
                    date_billed = date_billed.replace(tzinfo=None)
                    date_billed = date_billed.date()
                    days_to_pay = payment_date - date_billed
                    print(payment_date)
                    days_to_pay = abs((days_to_pay).days)
                    Workorder.objects.filter(pk=int(x)).update(paid_in_full=1, date_paid=date, open_balance=0, amount_paid = amount.total_balance, days_to_pay = days_to_pay, payment_id = payment_id)
                    remainder = remainder - amount.open_balance
                    print('Remainder')
                    print(remainder)
                    #Save Payment History
                    p = WorkorderPayment(workorder_id=int(x), payment_id=payment_id, payment_amount=amount.total_balance, date=payment_date)
                    print()
                    print(payment_date)
                    p.save()
                print(remainder)
                Payments.objects.filter(pk=payment_id).update(available=remainder)
                # if remainder > 0:
                #     Payments.objects.filter(pk=payment_id).update(available=remainder)
                # else:
                #     Payments.objects.filter(pk=payment_id).update(available=remainder)
                print(customer)
                cust = Customer.objects.get(id=customer)
                try:
                    credit = cust.credit + obj.amount
                except: 
                    credit = obj.amount
                credit = credit - payment_total
                open_balance = Workorder.objects.filter(customer_id=customer).exclude(completed=0).exclude(paid_in_full=1).aggregate(sum=Sum('open_balance'))
                open_balance = list(open_balance.values())[0]
                print(open_balance)
                balance = open_balance
                if not balance:
                    balance = 0
                high_balance = cust.high_balance
                if not high_balance:
                    high_balance = 0
                 #   high_balance = open_balance - credit             
                print(high_balance)
                if high_balance > balance:
                    high_balance = high_balance
                else:
                    high_balance = balance
                print(high_balance)
                Customer.objects.filter(pk=customer).update(credit=credit, open_balance=open_balance, high_balance=high_balance)
                if modal == '1':
                    workorders = Workorder.objects.filter(customer=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
                    total_balance = workorders.filter().aggregate(Sum('open_balance'))
                    credits = Customer.objects.get(pk=customer)
                    credits = credits.credit
                    print(credits)
                    #customer = customer
                    print(customer)
                    # context = {
                    #     'pk': customer,
                    #     'customer':customer,
                    #     'total_balance':total_balance,
                    #     'credit':credits,
                    #     'workorders':workorders,
                    # }
                    credits = Customer.objects.get(pk=customer)
                    credits = credits.credit
                    if credits:
                        return redirect('finance:open_invoices', pk=customer)
                    else:
                        workorders = Workorder.objects.filter(customer=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
                        if workorders:
                            return redirect('finance:open_invoices', pk=customer)
                        #Update paid status
                        return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderVoid'})
                else:
                    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = PaymentForm
    context = {
        'paymenttype':paymenttype,
        'customers':customers,
        'form': form,
    }
    return render(request, 'finance/AR/modals/recieve_payment.html', context)

@login_required
def unrecieve_payment(request):
    paymenttype = PaymentType.objects.all()
    customers = Customer.objects.all().order_by('company_name')
    if request.method == "POST":
            customer = request.POST.get('customer')
            print(customer)
            check = request.POST.get('check_number')
            giftcard = request.POST.get('giftcard_number')
            refund = request.POST.get('refunded_invoice_number')
            amount = request.POST.get('amount')
            amount = int(amount)
            cust = Customer.objects.get(id=customer)
            credit = cust.credit - amount
            Customer.objects.filter(pk=customer).update(credit=credit)
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = PaymentForm
    context = {
        'paymenttype':paymenttype,
        'form': form,
        'customers':customers,
    }
    return render(request, 'finance/AR/modals/remove_payment.html', context)

@login_required
def payment_detail(request):
    if request.method == "GET":
        type = request.GET.get('payment_type')
        field = PaymentType.objects.get(id=type)
        if field:
            method = field.detail_field
        else:
            method = ''
        print(method)
        context = {
            'method':method,
        }
    return render(request, 'finance/AR/partials/payment_detail.html', context)

@login_required
def apply_payment(request):
    if request.method == "POST":
            cust = request.POST.get('customer')
            pk = request.POST.get('pk')
            payment = request.POST.get('payment')
            payment_id = payment
            print(payment)
            try:
                payment_detail = Payments.objects.get(pk=payment)
            except:
                #return render(request, 'finance/reports/modals/open_invoices.html')
                return redirect('finance:open_invoices', pk=cust, msg=1)
            print('Payment #')
            print(payment)
            customer = Customer.objects.get(id=cust)
            workorder = Workorder.objects.get(id=pk)
            hr_workorder = workorder.workorder
            amount_paid = workorder.amount_paid
            print('amount paid')
            print(amount_paid)
            partial = request.POST.get('partial_payment')
            total = workorder.total_balance
            date_billed = workorder.date_billed
            if not date_billed:
                date_billed = timezone.now()
            date = timezone.now()
            days_to_pay = date - date_billed
            days_to_pay = abs((days_to_pay).days)
            if days_to_pay < 0:
                days_to_pay = 0
            avg_days = Workorder.objects.filter(customer_id=cust).exclude(days_to_pay=0).aggregate(avg=Avg('days_to_pay'))
            avg_days = list(avg_days.values())[0]
            print(avg_days)
            print(days_to_pay)
            if not avg_days:
                avg_days = 0
            credit = customer.credit
            payment_available = payment_detail.available
            if partial:
                print('partial')
                print(partial)
                full_payment = 0
                partial = float(partial)
                partial = Decimal.from_float(partial)
                #if credit >= partial:
                print('Payment Available')
                print(payment_available)
                print(partial)
                partial = round(partial, 2)
                if payment_available >= partial:
                    print('yadda')
                    open = workorder.open_balance
                    paid = workorder.amount_paid
                    paid = round(paid, 2)
                    partial = round(partial, 2)
                    if paid:
                        paid = paid + partial
                    else:
                        paid = partial
                    print('paid')
                    print(paid)
                    print('total')
                    print(total)
                    if paid >= total:
                        partial = open
                        paid = total
                        full_payment = 1
                    open = open - partial
                    credit = credit - partial
                    available = payment_available - partial
                    print(full_payment)
                    Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, paid_in_full = full_payment, date_paid = date)
                    Payments.objects.filter(pk=payment_id).update(available=available)
                    #Save Payment History
                    p = WorkorderPayment(workorder_id=pk, payment_id=payment_id, payment_amount=partial, date=date)
                    p.save()
                    #open_balance = Workorder.objects.filter(customer_id=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
                    open_balance = Workorder.objects.filter(customer_id=cust).exclude(completed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
                    open_balance = list(open_balance.values())[0]
                    if open_balance:
                        open_balance = round(open_balance, 2)
                    else:
                        open_balance = 0
                    print(open_balance)
                    Customer.objects.filter(pk=cust).update(credit = credit, open_balance = open_balance)
                else:
                    return redirect('finance:open_invoices', pk=cust, msg=1)
                # Get info for open invoices modal
                print('modal area!!!!!')
                print('customer')
                print(cust)
                modal_workorders = Workorder.objects.filter(customer=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
                modal_total_balance = modal_workorders.filter().aggregate(Sum('open_balance'))
                modal_credits = Customer.objects.get(pk=cust)
                modal_credits = modal_credits.credit
                print(modal_credits)
                modal_customer = cust
                print(modal_customer)
                payments = Payments.objects.filter(customer=modal_customer).exclude(available=None).exclude(void=1)
                context = {
                    'payments':payments,
                    'customer':modal_customer,
                    'total_balance':modal_total_balance,
                    'credit':modal_credits,
                    'workorders':modal_workorders,
                }
                credits = Customer.objects.get(pk=cust)
                credits = credits.credit
                if credits:
                    return render(request, 'finance/reports/modals/open_invoices.html', context)
                else:
                    workorders = Workorder.objects.filter(customer=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
                    if workorders:
                        return render(request, 'finance/reports/modals/open_invoices.html', context)
                    #Update paid status
                    return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderVoid'})
                    #return render(request, 'finance/reports/modals/open_invoices.html', context)
            else:
                open = workorder.open_balance 
            #if credit >= open:
            if payment_available >= open:
                Workorder.objects.filter(pk=pk).update(open_balance = 0, amount_paid = total, paid_in_full = 1, date_paid = date, days_to_pay = days_to_pay)
                credit = credit - open
                open_balance = Workorder.objects.filter(customer_id=cust).exclude(completed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
                open_balance = list(open_balance.values())[0]
                if open_balance:
                    print('open balance')
                    print(open_balance)
                    open_balance = round(open_balance, 2)
                    print(open_balance)
                else:
                    open_balance = 0
                available = payment_available - open
                Payments.objects.filter(pk=payment_id).update(available=available)
                Customer.objects.filter(pk=cust).update(credit = credit, avg_days_to_pay = avg_days, open_balance = open_balance)
                #Save Payment History
                p = WorkorderPayment(workorder_id=pk, payment_id=payment_id, payment_amount=open, date=date)
                p.save()
                # Get info for open invoices modal
                print('modal area!!!!!')
                print('customer')
                print(cust)
                modal_workorders = Workorder.objects.filter(customer=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
                modal_total_balance = modal_workorders.filter().aggregate(Sum('open_balance'))
                modal_credits = Customer.objects.get(pk=cust)
                modal_credits = modal_credits.credit
                print(modal_credits)
                modal_customer = cust
                print(modal_customer)
                payments = Payments.objects.filter(customer=customer).exclude(available=None)
                context = {
                    'payments':payments,
                    'customer':modal_customer,
                    'total_balance':modal_total_balance,
                    'credit':modal_credits,
                    'workorders':modal_workorders,
                }
                credits = Customer.objects.get(pk=cust)
                credits = credits.credit
                if credits:
                    return render(request, 'finance/reports/modals/open_invoices.html', context)
                else:
                    workorders = Workorder.objects.filter(customer=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
                    if workorders:
                        return render(request, 'finance/reports/modals/open_invoices.html', context)
                    #Update paid status
                    return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderVoid'})
                    #return render(request, 'finance/reports/modals/open_invoices.html', context)
            else:
                return redirect('finance:open_invoices', pk=cust, msg=1)
    
    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})

@login_required
def unapply_payment(request):
    if request.method == "POST":
        cust = request.POST.get('customer')
        pk = request.POST.get('workorder_pk')
        print(pk)
        customer = Customer.objects.get(id=cust)
        workorder = Workorder.objects.get(id=pk)
        print(customer)
        print(workorder)
        print(pk)
        
        # #This isn't working yet, needs to be further worked out
        # try:
        #     WorkorderPayment.objects.filter(workorder_id=pk).update(void=1)
        #     payment = WorkorderPayment.objects.filter(workorder_id=pk)
        # except:
        #     pass
        total = workorder.total_balance
        #open = workorder.open_balance
        paid = workorder.amount_paid
        credit = customer.credit + paid
        Workorder.objects.filter(pk=pk).update(open_balance = total, amount_paid = 0, paid_in_full = 0)
        #open_balance = Workorder.objects.filter(customer_id=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
        open_balance = Workorder.objects.filter(customer_id=cust).exclude(completed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
        open_balance = list(open_balance.values())[0]
        open_balance = round(open_balance, 2)
        print(open_balance)
        Customer.objects.filter(pk=cust).update(credit = credit, open_balance = open_balance)
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
                

@login_required
def apply_other(request, cust=None):
    if request.method == "GET":
        customer = cust
        print(customer)
    if request.method == "POST":
            customer = request.POST.get('customer')
            amount = request.POST.get('amount')
            if not amount:
                print('no amount')
                form = AppliedElsewhereForm
                message= 'Please enter an amount'
                context = {
                    'form': form,
                    'customer':customer,
                    'message':message,
                }
                return render(request, 'finance/AR/modals/apply_elsewhere.html', context)
            else:
                print(amount)
            print(1)
            customer = request.POST.get('customer')
            print(customer)
            form = AppliedElsewhereForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.customer_id = customer
                print(customer)
                cust = Customer.objects.get(id=customer)
                try:
                    credit = cust.credit - obj.amount
                    if credit < 0:
                        message = 'Customer only has credit of:'
                        credit = cust.credit
                        context = {
                            'form': form,
                            'customer':customer,
                            'message':message,
                            'credit':credit,
                        }
                        return render(request, 'finance/AR/modals/apply_elsewhere.html', context)
                    print('credit')
                    print(credit)
                except: 
                    credit = obj.amount
                    print(2)
                obj.save()
                Customer.objects.filter(pk=customer).update(credit=credit)
                print(3)
                #return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
                #return render(request, 'finance/reports/modals/open_invoices.html', pk=customer)
                return redirect('finance:open_invoices', pk=customer)
            else:
                print(form.errors)
    form = AppliedElsewhereForm
    context = {
        'form': form,
        'customer':customer,
    }
    return render(request, 'finance/AR/modals/apply_elsewhere.html', context)

# @login_required
# def add_bill_payable(request):
#     form = AccountsPayableForm(request.POST or None)
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             if form.is_valid():
#                 obj = form.save(commit=False)
#                 date_due = request.POST.get('date_due')
#                 invoice_date = request.POST.get('invoice_date')
#                 if not date_due:
#                     date = datetime.strptime(invoice_date, "%m/%d/%Y")
#                     #d = timedelta(days=30)
#                     date_due = date + timedelta(days=30)
#                     obj.date_due = date_due
#                 obj.save()
#                 messages.success(request, "Record Added...")
#                 return redirect('finance:add_bill_payable')
#         bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
#         vendors = Vendor.objects.all()
#         context = {
#             'vendors':vendors,
#             'form':form,
#             'bills':bills,
#         }
#         return render(request, 'finance/AP/add_ap.html', context)
#     else:
#         messages.success(request, "You must be logged in")
#         return redirect('home')

@login_required  
def add_daily_sale(request):
    form = DailySalesForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added...")
                return redirect('finance:add_daily_sale')
        return render(request, 'finance/reports/add_daily_sale.html', {'form':form})
    else:
        messages.success(request, "You must be logged in")
        return redirect('home')

@login_required   
def view_daily_sales(request):
    sales_list = DailySales.objects.all()
    return render(request, 'finance/reports/view_sales.html',
        {'sales_list': sales_list})

@login_required
def view_bills_payable(request):
    bills_list = AccountsPayable.objects.all().order_by('-invoice_date')
    return render(request, 'finance/AP/view_bills.html',
        {'bill_list': bills_list})

@login_required
def complete_not_billed(request):
    listing = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(void=1).order_by('hr_customer')
    print(listing)
    context = {
        'listing':listing,
    }
    return render(request, 'finance/reports/complete_not_billed.html', context)


# aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
# #         today = timezone.now()
# #         for x in aging:
# #             if not x.date_billed:
# #                 x.date_billed = today
# #             age = x.date_billed - today
# #             age = abs((age).days)
# #             print(type(age))
# #             Workorder.objects.filter(pk=x.pk).update(aging = age)

@login_required
def ar_aging(request):
    #Most of this function was moved to a cronjob
    update_ar = request.GET.get('up')
    print('update')
    print(update_ar)
    #customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
    today = timezone.now()
    customers = Customer.objects.all()
    ar = Araging.objects.all()
    workorders = Workorder.objects.filter().exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1)
    # for x in workorders:
    #     #print(x.id)
    #     if not x.date_billed:
    #         x.date_billed = today
    #     age = x.date_billed - today
    #     age = abs((age).days)
    #     print(age)
    #     Workorder.objects.filter(pk=x.pk).update(aging = age)
    total_balance = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    # for x in customers:
    #     try:
    #         #Get the Araging customer and check to see if aging has been updated today
    #         modified = Araging.objects.get(customer=x.id)
    #         print(x.company_name)
    #         day = today.strftime('%Y-%m-%d')
    #         day = str(day)
    #         date = str(modified.date)
    #         print(day)
    #         print(date)
    #         if day == date:
    #             #Don't update, as its been done today
    #             print('today')
    #             update = 0
    #             if update_ar == '1':
    #                 print('update')
    #                 update = 1
    #         else:
    #             update = 1
    #     except:
    #         update = 1
    #     #Update the Araging that needs to be done
    #     if update == 1:
    #         if Workorder.objects.filter(customer_id = x.id).exists():
    #             current = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
    #             try:
    #                 current = list(current.values())[0]
    #             except:
    #                 current = 0
    #             thirty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
    #             try: 
    #                 thirty = list(thirty.values())[0]
    #             except:
    #                 thirty = 0
    #             sixty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
    #             try:
    #                 sixty = list(sixty.values())[0]
    #             except:
    #                 sixty = 0
    #             ninety = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
    #             try:
    #                 ninety = list(ninety.values())[0]
    #             except:
    #                 ninety = 0
    #             onetwenty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
    #             try:
    #                 onetwenty = list(onetwenty.values())[0]
    #             except:
    #                 onetwenty = 0
    #             total = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    #             try:
    #                 total = list(total.values())[0]
    #             except:
    #                 total = 0
    #             try: 
    #                 obj = Araging.objects.get(customer_id=x.id)
    #                 Araging.objects.filter(customer_id=x.id).update(hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
    #             except:
    #                 obj = Araging(customer_id=x.id,hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
    #                 obj.save()
    ar = Araging.objects.all().order_by('hr_customer')
    #total_current = Araging.objects.filter().aggregate(Sum('current'))
    total_current = ar.filter().aggregate(Sum('current'))
    total_thirty = ar.filter().aggregate(Sum('thirty'))
    total_sixty = ar.filter().aggregate(Sum('sixty'))
    total_ninety = ar.filter().aggregate(Sum('ninety'))
    total_onetwenty = ar.filter().aggregate(Sum('onetwenty'))
    print(total_current)
    
    #print(ar)
    context = {
        'total_current':total_current,
        'total_thirty':total_thirty,
        'total_sixty':total_sixty,
        'total_ninety':total_ninety,
        'total_onetwenty':total_onetwenty,
        'total_balance':total_balance,
        'ar': ar,
    }
    return render(request, 'finance/reports/ar_aging.html', context)

@login_required
def krueger_ar_aging(request):
    #Most of this function was moved to a cronjob
    update_ar = request.GET.get('up')
    print('update')
    print(update_ar)
    #customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
    today = timezone.now()
    customers = Customer.objects.all()
    ar = Krueger_Araging.objects.all()
    workorders = Workorder.objects.filter().exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(internal_company='LK Design')
    # for x in workorders:
    #     #print(x.id)
    #     if not x.date_billed:
    #         x.date_billed = today
    #     age = x.date_billed - today
    #     age = abs((age).days)
    #     print(age)
    #     Workorder.objects.filter(pk=x.pk).update(aging = age)
    total_balance = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).filter(internal_company='Krueger Printing').aggregate(Sum('open_balance'))
    print(total_balance['open_balance__sum'] or 0)
    invoices = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).filter(internal_company='Krueger Printing')
    for x in invoices:
        print(x.id)
    # for x in customers:
    #     try:
    #         #Get the Araging customer and check to see if aging has been updated today
    #         modified = Araging.objects.get(customer=x.id)
    #         print(x.company_name)
    #         day = today.strftime('%Y-%m-%d')
    #         day = str(day)
    #         date = str(modified.date)
    #         print(day)
    #         print(date)
    #         if day == date:
    #             #Don't update, as its been done today
    #             print('today')
    #             update = 0
    #             if update_ar == '1':
    #                 print('update')
    #                 update = 1
    #         else:
    #             update = 1
    #     except:
    #         update = 1
    #     #Update the Araging that needs to be done
    #     if update == 1:
    #         if Workorder.objects.filter(customer_id = x.id).exists():
    #             current = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
    #             try:
    #                 current = list(current.values())[0]
    #             except:
    #                 current = 0
    #             thirty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
    #             try: 
    #                 thirty = list(thirty.values())[0]
    #             except:
    #                 thirty = 0
    #             sixty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
    #             try:
    #                 sixty = list(sixty.values())[0]
    #             except:
    #                 sixty = 0
    #             ninety = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
    #             try:
    #                 ninety = list(ninety.values())[0]
    #             except:
    #                 ninety = 0
    #             onetwenty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
    #             try:
    #                 onetwenty = list(onetwenty.values())[0]
    #             except:
    #                 onetwenty = 0
    #             total = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    #             try:
    #                 total = list(total.values())[0]
    #             except:
    #                 total = 0
    #             try: 
    #                 obj = Araging.objects.get(customer_id=x.id)
    #                 Araging.objects.filter(customer_id=x.id).update(hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
    #             except:
    #                 obj = Araging(customer_id=x.id,hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
    #                 obj.save()
    ar = Krueger_Araging.objects.all().order_by('hr_customer')
    #total_current = Araging.objects.filter().aggregate(Sum('current'))
    total_current = ar.filter().aggregate(Sum('current'))
    total_thirty = ar.filter().aggregate(Sum('thirty'))
    total_sixty = ar.filter().aggregate(Sum('sixty'))
    total_ninety = ar.filter().aggregate(Sum('ninety'))
    total_onetwenty = ar.filter().aggregate(Sum('onetwenty'))
    print(total_current)
    
    #print(ar)
    context = {
        'total_current':total_current,
        'total_thirty':total_thirty,
        'total_sixty':total_sixty,
        'total_ninety':total_ninety,
        'total_onetwenty':total_onetwenty,
        'total_balance':total_balance,
        'ar': ar,
    }
    return render(request, 'finance/reports/krueger_ar_aging.html', context)

@login_required
def krueger_ar(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'LK Design').exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('printleader_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/krueger_ar.html', context)

@login_required
def lk_ar(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'Krueger Printing').exclude(internal_company = 'Office Supplies').exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('lk_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/lk_ar.html', context)

@login_required
def all_printleader(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'LK Design').exclude(internal_company = 'Office Supplies').exclude(quote=1).exclude(void=1).order_by('-printleader_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/all_printleader.html', context)

@login_required
def all_open_printleader(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'LK Design').exclude(internal_company = 'Office Supplies').exclude(quote=1).exclude(void=1).exclude(paid_in_full=1).order_by('printleader_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/all_open_printleader.html', context)

@login_required
def all_lk(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'Krueger Printing').exclude(internal_company = 'Office Supplies').exclude(quote=1).exclude(void=1).order_by('-lk_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/all_lk.html', context)

@login_required
def open_invoices(request, pk, msg=None):
   workorders = Workorder.objects.filter(customer=pk).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
   payments = Payments.objects.filter(customer=pk).exclude(available = None).exclude(void = 1)
   total_balance = workorders.filter().aggregate(Sum('open_balance'))
   credits = Customer.objects.get(pk=pk)
   credits = credits.credit
   print(credits)
   customer = pk
   if msg:
       message = "Please select a different payment"
   else:
       message = ''
   context = {
       'message':message,
       'payments':payments,
       'customer':customer,
       'total_balance':total_balance,
       'credit':credits,
       'workorders':workorders,
   }
   return render(request, 'finance/reports/modals/open_invoices.html', context)

@login_required
def open_invoices_recieve_payment(request, pk, msg=None):
    if msg:
       message = "The payment amount is less than the workorders selected"
    else:
       message = ''
    workorders = Workorder.objects.filter(customer=pk).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    #total_balance = total_balance.total
    #print(total_balance)
    customer = Customer.objects.get(id=pk)
    #customer = 
    paymenttype = PaymentType.objects.all()
    form = PaymentForm

    context = {
        'total_balance':total_balance,
        'workorders':workorders,
        'paymenttype':paymenttype,
        'customer':customer,
        'form': form,
        'message': message,

    }
    return render(request, 'finance/reports/modals/open_invoice_recieve_payment.html', context)

@login_required
def payment_history(request):
    if request.method == "GET":
        customer = request.GET.get('customer')
        payment = Payments.objects.filter(customer=customer).exclude(void=1).exclude(available=0).order_by('-date')
        context = {
            'payment':payment,
            'customer':customer,
        }
    return render(request, 'finance/AR/partials/payment_history.html', context)

@login_required
def remove_payment(request, pk=None):
    customers = Customer.objects.filter().exclude(credit__lte=0).exclude(credit=None).order_by('company_name')
    if request.method == "POST":
        Payments.objects.filter(pk=pk).update(void = 1)
        details = Payments.objects.get(pk=pk)
        amount = details.available
        customer = details.customer.id
        cust = Customer.objects.get(id=customer)
        print(amount)
        print(cust)
        print(customer)
        credit = cust.credit - amount
        print(cust.credit)
        Customer.objects.filter(pk=details.customer.id).update(credit=credit)
        cust = Customer.objects.get(id=customer)
        print(cust.credit)
        #return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    context = {
        'customers':customers,
    }
    return render(request, 'finance/AR/modals/remove_payment.html', context)



############################################
###########

# AP Invoices

###########
#############################################

@login_required
def add_invoice(request, vendor=None):
    form = AddInvoiceForm()
    vendors = Vendor.objects.all()
    if request.method == "POST":
        form = AddInvoiceForm(request.POST)
        if form.is_valid():
            vendor = request.POST.get('vendor')
            #vendor = Vendor.objects.filter(pk=vendor)
            form.instance.vendor_id = vendor
            form.save()
            invoice = form.instance.pk
            return redirect ('finance:invoice_detail', id=invoice)
        else:
            print(form.errors)
        #invoices = RetailInvoices.objects.all().order_by('invoice_date')
        #print(vendor)
        # context = {
        #     'invoices': invoices,
        # }
    #Limit vendors, but this is currently not being used
    #vendors = Vendors.objects.filter(supplier=1)
    if vendor:
        bills = AccountsPayable.objects.filter().order_by('-invoice_date')
        balance = AccountsPayable.objects.filter().exclude(paid=1).aggregate(Sum('total'))
        calculated_total = AccountsPayable.objects.filter().exclude(paid=1).aggregate(Sum('calculated_total'))
    else:
        bills = AccountsPayable.objects.filter().exclude(vendor=23).order_by('-invoice_date') 
        balance = AccountsPayable.objects.filter().exclude(paid=1).exclude(vendor=23).aggregate(Sum('total'))
        calculated_total = AccountsPayable.objects.filter().exclude(paid=1).exclude(vendor=23).aggregate(Sum('calculated_total'))  
    context = {
        'balance': balance,
        'calculated_total': calculated_total,
        'form': form,
        'bills':bills,
        'vendors':vendors,
        #'categories': categories
    }
    return render (request, "finance/AP/add_ap.html", context)

def edit_invoice(request, invoice=None, drop=None):
    print('invoice')
    print(invoice)
    pk=invoice
    print(drop)
    if request.method == "POST":
        instance = AccountsPayable.objects.get(id=pk)
        form = EditInvoiceForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            #InvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
            
            return redirect ('finance:add_invoice') 
            #return HttpResponse(status=204, headers={'HX-Trigger': 'itemChanged'})         
        else:        
            messages.success(request, "Something went wrong")
            return redirect ('finance:add_invoice')
    obj = get_object_or_404(AccountsPayable, id=invoice)
    form = EditInvoiceForm(instance=obj)
    bills = AccountsPayable.objects.filter(pk=invoice).exclude(paid=1).order_by('invoice_date')
    #balance = AccountsPayable.objects.filter().exclude(paid=1).aggregate(Sum('total'))
    #calculated_total = AccountsPayable.objects.filter().exclude(paid=1).aggregate(Sum('calculated_total'))
    vendors = Vendor.objects.all()
    context = {
        #'balance': balance,
        #'calculated_total': calculated_total,
        'vendors':vendors,
        'pk':pk,
        'bills':bills,
        'form':form
    }
    return render (request, "finance/AP/edit_invoice.html", context)

def edit_invoice_modal(request, invoice=None):
    pk=invoice
    if request.method == "POST":
        instance = AccountsPayable.objects.get(id=pk)
        form = AddInvoiceForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            #InvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemChanged'}) 
            #return redirect ('finance:add_invoice')         
        else:        
            messages.success(request, "Something went wrong")
            return redirect ('finance:add_invoice')
    obj = get_object_or_404(AccountsPayable, id=invoice)
    form = AddInvoiceForm(instance=obj)
    bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
    context = {
        'pk':pk,
        'bills':bills,
        'form':form
    }
    return render (request, "finance/AP/modals/edit_invoice_modal.html", context)




# @login_required
# def add_bill_payable(request):
#     form = AccountsPayableForm(request.POST or None)
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             if form.is_valid():
#                 obj = form.save(commit=False)
#                 date_due = request.POST.get('date_due')
#                 invoice_date = request.POST.get('invoice_date')
#                 if not date_due:
#                     date = datetime.strptime(invoice_date, "%m/%d/%Y")
#                     #d = timedelta(days=30)
#                     date_due = date + timedelta(days=30)
#                     obj.date_due = date_due
#                 obj.save()
#                 messages.success(request, "Record Added...")
#                 return redirect('finance:add_bill_payable')
#         bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
#         vendors = Vendor.objects.all()
#         context = {
#             'vendors':vendors,
#             'form':form,
#             'bills':bills,
#         }
#         return render(request, 'finance/AP/add_ap.html', context)
#     else:
#         messages.success(request, "You must be logged in")
#         return redirect('home')
    



@login_required
def invoice_detail(request, id=None):
    if request.method == "POST":
        # invoice = request.POST.get('invoice')
        # invoice_item = request.POST.get('pk')
        # print('invoice_item')
        # print(invoice_item)
        vendor = request.POST.get('vendor')
        variation = request.POST.get('variation')
        ipn = request.POST.get('internal_part_number')
        base_unit = InventoryMaster.objects.get(pk=ipn)
        base_unit = base_unit.primary_base_unit.id
        ppm = request.POST.get('ppm')
        print('ppm')
        print(ppm)
        unit = request.POST.get('unit')
        item_qty = request.POST.get('variation_qty')
        edit = request.POST.get('edit')
        if unit:
            variation_qty = item_qty
            variation = unit
            variation_qty = int(variation_qty)
            var = InventoryQtyVariations(inventory=InventoryMaster.objects.get(pk=ipn), variation=Measurement.objects.get(pk=variation) , variation_qty=variation_qty) 
            var.save()
            print('var saved')
            print(var.pk)
            var = var.pk
        else:
            var = ''
            v = InventoryQtyVariations.objects.get(id=variation)
            variation_qty = v.variation_qty
        # print(variation)
        # print(ipn)
        
        # print('v')
        # print(v)
        #vendor = int(vendor)
        invoice = id
        print('id')
        print(id)
        if edit == '1':
            pass
            invoice_item = request.POST.get('pk')
            obj = InvoiceItem.objects.get(pk=invoice_item)
            form = AddInvoiceItemForm(request.POST, instance=obj)
        else:
            form = AddInvoiceItemForm(request.POST)
        if form.is_valid():
            print(invoice)
            qty = form.instance.invoice_qty * variation_qty
            if form.instance.invoice_unit_cost:
                if ppm == '1':
                    price_ea = form.instance.invoice_unit_cost / 1000
                    print('price each ppm')
                    print(price_ea)
                else:
                    ppm = '0'
                    price_ea = form.instance.invoice_unit_cost / variation_qty
                    print('price each')
                    print(price_ea)
            else:
                price_ea = 0
                ppm = 0
            vpn = form.instance.vendor_part_number
            description = form.instance.description
            form.instance.qty = qty
            form.instance.unit_cost = price_ea
            form.instance.invoice_id = invoice
            print(qty)
            print(price_ea)
            print(invoice)
            if var:
                form.instance.invoice_unit = InventoryQtyVariations.objects.get(pk=var)
            else:
                form.instance.invoice_unit = InventoryQtyVariations.objects.get(id=variation)
            #form.instance.invoice_unit = v
            form.instance.ppm = ppm
            line_total = qty * price_ea
            form.instance.line_total = line_total
            #form.instance.variation_qty = v.variation_qty
            form.save()
            invoice_date = form.instance.created
            invoice_item = form.instance.pk
            print('invoice_item')
            print(invoice_item)
            vpn_up = request.POST.get('vpn_update')
            desc_up = request.POST.get('description_update')
            print('vpn_update')
            print(vpn_up)
            print('desc update')
            print(desc_up)
            if vpn_up or desc_up == '1':
                VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=ipn).update(vendor_part_number=vpn, description=description)
            name = form.instance.name
            print(name)
            print(vendor)
            print('here')
            print(invoice_item)
            print(variation)
            item_v = InventoryQtyVariations.objects.get(pk=variation)
            print(item_v)
            item_variation = item_v.variation.id
            print('variation')
            print(item_variation)
            invoice_date = AccountsPayable.objects.get(pk=invoice)
            invoice_date = invoice_date.invoice_date
            print('invoice item')
            print(invoice_item)
            # try:
            #     item = get_object_or_404(AllInvoiceItem, invoice_item=invoice_item)
            #     #item = AllInvoiceItem.objects.filter(invoice_item=invoice_item)
            #     print('123')
            #     print(item)
            # except:
            #     obj = AllInvoiceItem(invoice_item=InvoiceItem.objects.get(pk=invoice_item), invoice_id=invoice, internal_part_number=InventoryMaster.objects.get(id=ipn), purchase_date=invoice_date, qty=qty, unit_cost=price_ea, vendor=Vendor.objects.get(pk=vendor), unit=Measurement.objects.get(pk=base_unit), line_total=line_total)
            #     #inventory=InventoryMaster.objects.get(pk=pk)
            #     obj.save()  
            #     item = ''
            # if item:
            #     AllInvoiceItem.objects.filter(invoice_item=invoice_item).update(invoice_id=invoice, internal_part_number=InventoryMaster.objects.get(id=ipn), purchase_date=invoice_date, qty=qty, unit_cost=price_ea, vendor=Vendor.objects.get(pk=vendor), unit=Measurement.objects.get(pk=base_unit), line_total=line_total)


            print('invoice')
            print(invoice)
            total = InvoiceItem.objects.filter(invoice=invoice).aggregate(Sum('line_total'))
            total = list(total.values())[0]
            total = Decimal(total)
            AccountsPayable.objects.filter(pk=invoice).update(calculated_total=total)
            # print('running total')
            # print(instance.invoice.id)
            # total = InvoiceItem.objects.filter(invoice=instance.invoice.id).aggregate(Sum('line_total'))
            # print(total)
            # total = list(total.values())[0]
            # total = Decimal(total)
            # AccountsPayable.objects.filter(pk=instance.invoice.id).update(calculated_total=total)



        else:
            print(form.errors)
        invoice = get_object_or_404(AccountsPayable, id=invoice)
        print('djska')
        print(invoice)
        items = InvoiceItem.objects.filter(invoice_id = invoice)
        print(items)
        return redirect ('finance:invoice_detail', id=id)
    invoice = get_object_or_404(AccountsPayable, id=id)
    vendor = Vendor.objects.get(id=invoice.vendor.id)
    print(vendor)
    print(vendor.id)
    items = InvoiceItem.objects.filter(invoice_id = id)
    context = {
        'vendor':vendor,
        'invoice': invoice,
        'items': items,
    }
    return render(request, 'finance/AP/invoice_detail.html', context)

def invoice_detail_highlevel(request, id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)
    vendor = Vendor.objects.get(id=invoice.vendor.id)
    print(vendor)
    print(vendor.id)
    items = InvoiceItem.objects.filter(invoice_id = id)
    context = {
        'vendor':vendor,
        'invoice': invoice,
        'items': items,
    }
    return render(request, 'finance/AP/invoice_detail_highlevel.html', context)


def add_invoice_item(request, invoice=None, vendor=None, type=None):
    if vendor:
        item_id = request.GET.get('name')
        if item_id:
            print('hello')
            # print(item_id)
            # print(vendor)
            try:
                item = get_object_or_404(VendorItemDetail, internal_part_number=item_id, vendor=vendor)
                try:
                    variations = InventoryQtyVariations.objects.filter(inventory=item_id).order_by('variation_qty')
                except:
                    variations = ''
                name = item.name
                ipn = item_id
                vpn = item.vendor_part_number
                description = item.description
                primary_base_unit = item.internal_part_number.primary_base_unit
                if not primary_base_unit:
                    primary_base_unit = 'No Primary Base Unit'
                context = {
                    'primary_base_unit':primary_base_unit,
                    'variations':variations,
                    'name': name,
                    'vpn': vpn,
                    'ipn': ipn,
                    'description': description,
                    'vendor':vendor,
                    'invoice':invoice,
                }

                return render (request, "finance/AP/partials/invoice_item_remainder.html", context)
            except:
                print('sorry')
                item = ''
                form = ''
                vendor = ''
            # print(vendor)
            form = AddInvoiceItemForm
            context = {
                'form':form,
                'vendor':vendor,
                'invoice':invoice,
            }
            return render (request, "finance/AP/partials/invoice_item_remainder.html", context)
    invoice = invoice
    vendor = AccountsPayable.objects.get(id=invoice)
    # print(vendor.vendor.name)
    vendor = vendor.vendor.id
    # print(vendor)
    #items = RetailInvoiceItem.objects.filter(vendor=vendor)
    print(type)
    print(vendor)
    if type == 1:
        print('hello')
        items = VendorItemDetail.objects.filter(vendor=vendor, non_inventory=1)
    elif type == 2:
        print('hello2')
        items = VendorItemDetail.objects.filter(vendor=vendor, online_store=1)
    else:
        print('hello3')
        items = VendorItemDetail.objects.filter(vendor=vendor, non_inventory=0)
    for x in items:
        print(x)
    form = AddInvoiceItemForm
    context = {
        'items': items,
        'invoice': invoice,
        'vendor': vendor,
        'form': form,
    }
    return render (request, "finance/AP/partials/add_invoice_item.html", context)




def edit_invoice_item(request, invoice=None, id=None):
    print(id)
    print(invoice)
    item = InvoiceItem.objects.get(id=id)
    print(item)
    print(item.pk)
    pk = item.pk
    if request.method == "POST":
        invoice = request.POST.get('invoice')
        instance = InvoiceItem.objects.get(id=pk)
        form = AddInvoiceItemForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
        # invoice = item.invoice_id
        # print('invoice')
        # print(invoice)
        # print('here')
        # #vendor = request.POST.get('vendor')
        # form = AddInvoiceItemForm(request.POST)
        # if form.is_valid():
        #     #form.save()
        #     name = form.instance.name
        #     vendor_part_number = form.instance.vendor_part_number
        #     description = form.instance.description
        #     unit_cost = form.instance.unit_cost
        #     qty = form.instance.qty
        #     InvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
        #     # print('IPN')
            # print(item.internal_part_number.id)
            # print('Vendor')
            # print(item.vendor.id)
            
            # vendor_item = RetailVendorItemDetail.objects.get(internal_part_number=item.internal_part_number.id, vendor=item.vendor.id)
            # print(vendor_item.pk)
            # try:
            #     vendor_item = VendorItemDetail.objects.get(internal_part_number=item.internal_part_number.id, vendor=item.vendor.id)
            #     print(vendor_item.pk)
            # except:
            #     print('failed')
            # if vendor_item:
            #     high_price = vendor_item.high_price
            #     print(high_price)
            #     current_price = form.instance.unit_cost
            #     print(current_price)
            #     high_price = int(high_price)
            #     current_price = int(current_price)
            #     print('issue')
            #     if high_price == 'None':
            #         hp = 0
            #         print(1)
            #     else:
            #         hp = high_price
            #     print('issue')
            #     if current_price == 'None':
            #         cp = 0
            #         print(2)
            #     else:
            #         cp = current_price
            #     print('issue')
            #     #updated = datetime.now
            #     #print(updated)
            #     if not high_price:
            #         VendorItemDetail.objects.filter(pk=vendor_item.pk).update(high_price=cp)
            #         print(3)
            #     if current_price > high_price:
            #         print(high_price)
            #         print(hp)
            #         print(current_price)
            #         print(cp)
            #         VendorItemDetail.objects.filter(pk=vendor_item.pk).update(high_price=cp, updated=datetime.now()) 
            #     #RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=cp)
            #     print(high_price)
            #     print(hp)
            #     print(current_price)
            #     print(cp)
            #     print('something')
            #     print(invoice)
            return redirect ('finance:invoice_detail', id=invoice)
            
        else:
            
            messages.success(request, "Name, Unit Cost, and Qty are required")
            return redirect ('finance:invoice_detail', id=invoice)
    ipn = item.internal_part_number.id
    try:
        variations = InventoryQtyVariations.objects.filter(inventory=ipn)
    except:
        variations = ''
    name = item.name
    #variation = item.variation
    #variation_qty = item.variation_qty
    vpn = item.vendor_part_number
    description = item.description
    unit_cost = item.unit_cost
    qty = item.qty
    pk = item.pk
    ipn = item.internal_part_number.id
    vendor = item.vendor.id
    print(variations)
    #form = AddInvoiceItemForm(instance=item)
    # if request.method == "POST":
    #     invoice = request.POST.get('invoice')
    #     vendor = request.POST.get('vendor')
    #     #vendor = int(vendor)
    #     id = invoice
    #     form = AddInvoiceItemForm(request.POST)
    #     if form.is_valid():
    #         form.instance.invoice_id = invoice
    #         form.save()
    #         name = form.instance.name
    #         try:
    #             item = RetailVendorItemDetail.objects.get(name=name, vendor_id=vendor)
    #             print(item.pk)
    #             high_price = item.high_price
    #             print(high_price)
    #             current_price = form.instance.unit_cost
    #             print(current_price)
    #             if not high_price:
    #                 RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=current_price, updated=datetime.now())
    #             elif current_price > high_price:
    #                 RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=current_price, updated=datetime.now())            
    #         except:
    #             print(vendor)
    #             RetailVendorItemDetail.objects.create(
    #                 vendor_id = vendor,
    #                 name=name,
    #                 vendor_part_number = form.instance.vendor_part_number,
    #                 description = form.instance.description,
    #                 internal_part_number = form.instance.internal_part_number,
    #                 high_price = form.instance.unit_cost
    #                 )
    #     else:
    #         print(form.errors)
    item = InvoiceItem.objects.filter(id=id)
    print(item)
    context = {
        'variations':variations,
        'item':item,
        'name':name,
        #'variation':variation,
        #'variation_qty':variation_qty,
        'vendor':vendor,
        'vpn':vpn,
        'description':description,
        'unit_cost':unit_cost,
        'qty':qty,
        'pk':pk,
        'ipn':ipn,
        'invoice':invoice
        #'form':form
    }
    return render (request, "finance/AP/partials/edit_invoice_item.html", context)

@login_required
def delete_invoice_item(request, id=None, invoice=None):
    print('invoice')
    print(invoice)
    print('id')
    print(id)
    item = get_object_or_404(InvoiceItem, id=id)
    item_delete = item
    vendor = item.vendor.id
    print(vendor)
    internal_part_number = item.internal_part_number.id
    print(11)
    print(internal_part_number)
    # print(vendor)
    items = InvoiceItem.objects.filter(vendor=vendor, internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
    print(12)
    print(items)
    price = list(items.values())[0]
    if price:
        print('1')
        print(price)
    else:
        print('no price')
    vendorprice = VendorItemDetail.objects.get(vendor=vendor, internal_part_number=internal_part_number)
    # # print('highprice')
    print('13')
    print(vendorprice.high_price)
    #Lower price for vendor item if highest price was deleted from invoice item
    if vendorprice.high_price > price:
         VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=internal_part_number).update(high_price=price, updated=datetime.now())
    #Lower price for inventory master if highest price from any vendor was removed
    overall_price = InvoiceItem.objects.filter(internal_part_number=internal_part_number).aggregate(Max('unit_cost'))
    op = list(overall_price.values())[0]
    master_price = InventoryMaster.objects.get(pk=internal_part_number)
    master_price = master_price.high_price
    print('master')
    print(master_price)
    print('op')
    print(op)
    if master_price > op:
        m = price * 1000
        InventoryMaster.objects.filter(pk=internal_part_number).update(high_price=price, unit_cost=price, price_per_m=m, updated=datetime.now())
        try:
            Inventory.objects.filter(internal_part_number=internal_part_number).update(unit_cost=price, price_per_m=m, updated=datetime.now())
        except:
            pass
    # # print('hello')
    groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number)
    # high_price_list = []
    # list = []
    high_price_current = 0
    for x in groups:
        print('12')
        #InventoryPricingGroup.objects.filter(group=x.group).update(high_price=price)
        group_items = InventoryPricingGroup.objects.filter(group=x.group)
        for x in group_items:
            # print('13')
            price = InvoiceItem.objects.filter(internal_part_number=x.inventory.id).aggregate(Max('unit_cost'))
            price = list(items.values())[0]
            # print(price)
            if price > high_price_current:
                # print('deleted price')
                high_price_current = price
                # print(high_price_current)
            else:
                pass
                # print(price)
    price = high_price_current
    groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number)
    for x in groups:
        InventoryPricingGroup.objects.filter(group=x.group).update(high_price=price)
        group_items = InventoryPricingGroup.objects.filter(group=x.group)
        for x in group_items:
            y = InventoryMaster.objects.get(pk=x.inventory.id)
            if y.units_per_base_unit:
                cost = price / y.units_per_base_unit
                m = cost * 1000
            else:
                cost=0
                m = 0
            # print(x.inventory.id)
            InventoryMaster.objects.filter(pk=x.inventory.id).update(high_price=price, unit_cost=cost, price_per_m=m, updated=datetime.now())
            VendorItemDetail.objects.filter(vendor=vendor, internal_part_number=x.inventory.id).update(high_price=price, updated=datetime.now())
            Inventory.objects.filter(internal_part_number=x.inventory.id).update(unit_cost=cost, price_per_m=m, updated=datetime.now())
        print(x.inventory)
    item_delete.delete()
 
    return redirect ('finance:invoice_detail', id=invoice)

def add_item_to_vendor(request, vendor=None, invoice=None):
    print('vendor')
    print(vendor)
    print('something')
    if request.method == "POST":
        print('something')
        form = VendorItemDetailForm(request.POST)
        if form.is_valid():
            form.save()
            print('valid')
            invoice = request.POST.get('invoice')
            vendor_part_number = request.POST.get('vendor_part_number')
            vendor = request.POST.get('vendor')
            pk = form.instance.pk
            print(vendor)
            vendor_type = Vendor.objects.get(id=vendor)
            if vendor_type.retail_vendor == 1:
                VendorItemDetail.objects.filter(pk=pk).update(vendor=vendor, vendor_part_number=vendor_part_number)
            return redirect ('finance:invoice_detail', id=invoice)
        else:
            print(form.errors)
    form = VendorItemDetailForm
    #Get all inventory items
    items = InventoryMaster.objects.all()
    list = []
    #Go through inventory. If not matched with a vendor, add to select list
    print('lookup1')
    for x in items:
        try:
            #print('lookup1')
            obj = get_object_or_404(VendorItemDetail, internal_part_number=x.pk, vendor=vendor)
            #print(obj)
        except:
            list.append(x)
            #print('except')
            #print(x.pk)
    #print(list)
    context = {
        'form':form,
        'vendor': vendor,
        'invoice': invoice,
        'list':list,
        # 'items':items,
    }
    if not vendor:
        return render (request, "inventory/items/add_item_to_vendor.html", context)
    return render (request, "inventory/partials/add_item_to_vendor.html", context)

def add_inventory_item(request, vendor=None, invoice=None, baseitem=None):
    print(baseitem)
    form = InventoryMasterForm
    if not invoice:
        if request.method == "POST":
            form = InventoryMasterForm(request.POST)
            if form.is_valid():
                #print(form.data)
                print('yippie')
                #vendor = request.POST.get('primary_vendor')
                #form.instance.primary_vendor = vendor
                form.save()
                pk = form.instance.pk
                unit_cost = form.instance.unit_cost
                price_per_m = unit_cost * 1000
                print('Cost per M')
                print(price_per_m)
                InventoryMaster.objects.filter(pk=pk).update(high_price=unit_cost, price_per_m=price_per_m)
                item = InventoryMaster.objects.get(pk=pk)
                primary_unit = item.primary_base_unit.id
                units_per_base = item.units_per_base_unit
                variation = InventoryQtyVariations(inventory=InventoryMaster.objects.get(pk=pk), variation=Measurement.objects.get(id=primary_unit), variation_qty=units_per_base)
                variation.save()
                print(item.pk)
                vendor = item.primary_vendor
                name = item.name
                vpn = item.primary_vendor_part_number
                description = item.description
                supplies = item.supplies
                retail = item.retail
                non_inventory = item.non_inventory
                online_store = item.online_store
                if online_store:
                    print('Online Store')
                    print(online_store)
                print('Online Store Above')
                invoice = request.POST.get('invoice')
                print(vendor)
                item = VendorItemDetail(vendor=vendor, name=name, vendor_part_number=vpn, description=description, supplies=supplies, retail=retail, non_inventory=non_inventory, online_store=online_store, internal_part_number_id=item.pk )
                item.save()
                if online_store:
                    store_item = StoreItemDetails(item=InventoryMaster.objects.get(pk=pk))
                    store_item.save()
                baseitem = request.POST.get('baseitem')
                print(baseitem)
                print('123')
                if baseitem:
                    print('dsajk')
                    messages.success(request, ("Item has been added"))
                    return redirect ('finance:add_inventory_item', baseitem=1)
                    #return redirect ('finance:invoice_detail', id=invoice)
                if invoice is None:
                    return redirect ('finance:invoice_detail', id=invoice)
                #return redirect ('finance:retail_inventory_list')
                return redirect ('finance:invoice_detail', id=invoice)
        context = {
        'form':form,
        'invoice':invoice
        }
        print('test')
        #return redirect ('finance:view_bills_payable')
        if baseitem:
            print(baseitem)
            return render (request, "inventory/items/add_inventory_item.html", context)
        return render (request, "inventory/partials/add_inventory_item.html", context)
    context = {
        'form':form,
        'invoice':invoice
    }
    print(baseitem)
    if baseitem:
        print(baseitem)
        return render (request, "inventory/items/add_inventory_item.html", context)
    print(baseitem)
    return render (request, "inventory/partials/add_inventory_item.html", context)


def vendor_item_remainder(request, vendor=None, invoice=None):
    form = VendorItemDetailForm
    # invoice = invoice
    # vendor = vendor
    item_id = request.GET.get('item')
    print(item_id)
    if item_id:
        try:
            item = get_object_or_404(InventoryMaster, pk=item_id)
            print(item.id)
            print('hello')
            name = item.name
            description = item.description
            ipn = item.id
        except:
            print('sorry')
            #item = ''
            #form = ''
            vendor = ''
        print(vendor)
        form = AddInvoiceItemForm
        context = {
            'form':form,
            'name':name,
            'description':description,
            'ipn':ipn,
            'vendor':vendor,
            'invoice':invoice,
        }
        return render (request, "inventory/partials/vendor_item_remainder.html", context)


def bills_by_vendor(request):
    name = request.GET.get('name')
    vendor = request.GET.get('vendor')
    if name:
        vendor = name
    vendors = Vendor.objects.all()
    if vendor:
        open_bills = AccountsPayable.objects.filter(vendor=vendor).order_by('-invoice_date').exclude(paid=1)
        paid_bills = AccountsPayable.objects.filter(vendor=vendor).order_by('-invoice_date').exclude(paid=0)
        balance = AccountsPayable.objects.filter(vendor=vendor).exclude(paid=1).aggregate(Sum('total'))
        calculated_total = AccountsPayable.objects.filter(vendor=vendor).exclude(paid=1).aggregate(Sum('calculated_total'))
        context = {
            'open_bills':open_bills,
            'paid_bills':paid_bills,
            'balance': balance,
            'calculated_total': calculated_total,
        }
        return render (request, "finance/AP/partials/vendor_bills.html", context)
    vendors = Vendor.objects.all()
    context = {
        'vendors':vendors,
    }
    return render (request, "finance/AP/bills_by_vendor.html", context)


def bulk_edit_invoices(request, vendor=None):
    if request.method == "POST":
        form = BulkEditInvoiceForm(request.POST)
        if form.is_valid():
            payment = form.instance.payment_method
            check = form.instance.check_number
            if not check:
                check = ''
            vendor = request.POST.get('vendor')
            date = request.POST.get('date')
            date = datetime.strptime(date, '%m/%d/%Y')
            print(date)
            id_list = request.POST.getlist('payment')
            for x in id_list:
                print(x)
                invoice = AccountsPayable.objects.get(pk=x)
                print(invoice.total)
                amount = invoice.total
                AccountsPayable.objects.filter(pk=x).update(paid=True, amount_paid=amount, payment_method=payment, check_number=check, date_paid=date)
            return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderInfoChanged'})
    invoices = AccountsPayable.objects.filter(vendor=vendor).exclude(paid=1).order_by('-invoice_date')
    form = BulkEditInvoiceForm
    context = {
        'invoices':invoices,
        'form':form,
        'vendor':vendor,
    }
    return render (request, "finance/AP/modals/bulk_edit_invoices.html", context)




def payment_history(request):
    payments = Payments.objects.all().order_by('-date')
    context = {
        'payments':payments,
    }
    return render (request, "finance/reports/payment_history.html", context)


def sales_tax_payable(request):
    form = DateRangeForm()

    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            print("Start:", start_date)
            print("End:", end_date)

        workorders = Workorder.objects.filter(date_billed__range=(start_date, end_date)).order_by('date_billed')
        total_tax = workorders.aggregate(Sum('tax'))['tax__sum'] or 0
        invoice_total = workorders.aggregate(Sum('workorder_total'))['workorder_total__sum'] or 0
        invoice_subtotal = workorders.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
        
        taxable_workorders = workorders.exclude(tax__isnull=True).exclude(tax=0)
        total_taxs = taxable_workorders.aggregate(Sum('tax'))['tax__sum'] or 0
        taxable_total = taxable_workorders.aggregate(Sum('workorder_total'))['workorder_total__sum'] or 0
        
        exemptions = invoice_total - taxable_total

        context = {
            'form':form,
            'start_date':start_date,
            'workorders':workorders,
            'total_tax':total_tax,
            'total_taxs':total_taxs,
            'invoice_total':invoice_total,
            'invoice_subtotoal':invoice_subtotal,
            'exemptions':exemptions,
        }

        return render (request, "finance/reports/sales_tax_payable.html", context)

    context = {
            'form':form,
        }

    return render (request, "finance/reports/sales_tax_payable.html", context)


#     if request.method == "POST":
#             modal = request.POST.get('modal')
#             id_list = request.POST.getlist('payment')
#             payment_total = 0
#             for x in id_list:
#                 print('payment total')
#                 print(payment_total)
#                 t = Workorder.objects.get(pk=int(x))
#                 balance = t.open_balance
#                 payment_total = payment_total + balance


# @login_required
# def open_invoices_recieve_payment(request, pk, msg=None):
#     if msg:
#        message = "The payment amount is less than the workorders selected"
#     else:
#        message = ''
#     workorders = Workorder.objects.filter(customer=pk).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
#     total_balance = workorders.filter().aggregate(Sum('open_balance'))
#     #total_balance = total_balance.total
#     #print(total_balance)
#     customer = Customer.objects.get(id=pk)
#     #customer = 
#     paymenttype = PaymentType.objects.all()
#     form = PaymentForm

#     context = {
#         'total_balance':total_balance,
#         'workorders':workorders,
#         'paymenttype':paymenttype,
#         'customer':customer,
#         'form': form,
#         'message': message,

#     }
#     return render(request, 'finance/reports/modals/open_invoice_recieve_payment.html', context)





























# def unrecieve_payment(request):
#     paymenttype = PaymentType.objects.all()
#     customers = Customer.objects.all().order_by('company_name')
#     if request.method == "POST":
#             customer = request.POST.get('customer')
#             print(customer)
#             check = request.POST.get('check_number')
#             giftcard = request.POST.get('giftcard_number')
#             refund = request.POST.get('refunded_invoice_number')
#             amount = request.POST.get('amount')
#             amount = int(amount)
#             cust = Customer.objects.get(id=customer)
#             credit = cust.credit - amount
#             Customer.objects.filter(pk=customer).update(credit=credit)
#             return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
#     form = PaymentForm
#     context = {
#         'paymenttype':paymenttype,
#         'form': form,
#         'customers':customers,
#     }
#     return render(request, 'finance/AR/modals/remove_payment.html', context)



















            # obj, created = Araging.objects.update_or_create(
            #     customer_id=x.id,
            #     hr_customer=x.company_name,
            #     date=today,
            #     current=current
            # )
        #current = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer', 'customer_id').annotate(current_balance=Sum('open_balance'))
        #subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
        
        #current = customers.filter(customer_id = x.id).aggregate(Sum('open_balance'))
        # current = list(current.values())[0]
        # print(current)
        #print(current.current_bal)
        #print(current.sum)
        #print(open_balance__sum)
        #total.total_with_tax__sum
        #print(current)

    #     total_invoice = WorkorderItem.objects.filter(workorder_id=workorder).exclude(billable=0).aggregate(
    #         sum=Sum('total_with_tax'),
    #         tax=Sum('tax_amount'),
    #         )
    # #total_invoice = list(WorkorderItem.objects.aggregate(Sum('total_with_tax')).values())[0]
    # total = list(total_invoice.values())[0]
    # if not total:
    #     total = 0
    # total = round(total, 2)
    # tax = list(total_invoice.values())[1]






    




















# def ar_aging(request):
#     customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     current = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer').annotate(current_balance=Sum('open_balance'))
#     thirty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).values('hr_customer').annotate(thirty=Sum('open_balance'))
#     sixty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).values('hr_customer').annotate(sixty=Sum('open_balance'))
#     ninety = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).values('hr_customer').annotate(ninety=Sum('open_balance'))
#     onetwenty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).values('hr_customer').annotate(onetwenty=Sum('open_balance'))
#     total = customers.all().values('hr_customer').annotate(total_balance=Sum('open_balance'))

#     #total_balance = Workorder.objects.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
#     total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0

#     # Aggregate individual balances for each customer
#     individual_balances = Workorder.objects.values('hr_customer').annotate(
#         #total_balance=Sum('open_balance'),
#         total_balance=Subquery(total.filter(hr_customer=models.OuterRef('hr_customer')).values('total_balance')[:1]),
#         current=Subquery(current.filter(hr_customer=models.OuterRef('hr_customer')).values('current_balance')[:1]),
#         #current=Subquery(current),
#         thirty=Subquery(thirty.filter(hr_customer=models.OuterRef('hr_customer')).values('thirty')[:1]),
#         sixty=Subquery(sixty.filter(hr_customer=models.OuterRef('hr_customer')).values('sixty')[:1]),
#         ninety=Subquery(ninety.filter(hr_customer=models.OuterRef('hr_customer')).values('ninety')[:1]),
#         onetwenty=Subquery(onetwenty.filter(hr_customer=models.OuterRef('hr_customer')).values('onetwenty')[:1]),
#         ).order_by('hr_customer')
    
#     for x in individual_balances:
#         print(x)

#     context = {
#             'customers':customers,
#             'total_balance':total_balance,
#             'individual_balances':individual_balances,
#         }
#     return render(request, 'finance/reports/ar_aging.html', context)








# def ar_aging(request):
#     #balance = Workorder.objects.all.exclude(quote=1).aggregate(Sum('total_balance'))
#     customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)

#     # #aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
#     # today = timezone.now()
#     # for x in customers:
#     #     if not x.date_billed:
#     #         x.date_billed = today
#     #     age = x.date_billed - today
#     #     age = abs((age).days)
#     #     print(x.hr_customer)
#     #     print(type(age))
#     #     print(age)
#     #     #Workorder.objects.filter(pk=x.pk).update(aging = age)










#     current = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer').annotate(current_balance=Sum('open_balance'))
#     thirty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).values('customer_id').annotate(thirty=Sum('open_balance'))
#     sixty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).values('customer_id').annotate(sixty=Sum('open_balance'))
#     ninety = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).values('customer_id').annotate(ninety=Sum('open_balance'))
#     onetwenty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).values('customer_id').annotate(onetwenty=Sum('open_balance'))
#     total = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).values('customer_id').annotate(current_balance=Sum('open_balance'))
#     #cust = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     #balance = sum(customers.open_balance for customer in customers)

#     # print(list(current))
#     # for x in current:
#          #print(x.hr_customer)
#          #print(x.current_balance)
#         #print(x)
#     # Calculate the total balance
#     #total_balance = Workorder.objects.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
#     total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
        

#     # Aggregate individual balances for each customer
#     #individual_balances = Workorder.objects.values('hr_customer').annotate(total_balance=Sum('open_balance'))
#     #individual_balances = customers.values('hr_customer').annotate(total_balance=Sum('open_balance'), current=Subquery(current))
#     individual_balances = Workorder.objects.values('hr_customer').annotate(
#         total_balance=Sum('open_balance'),
#         # total_balance=Sum(
#         #     Case(
#         #         When(
#         #             billed = 0, # Exclude Workorders where billed is 0
#         #             paid_in_full = 1,
#         #             quote = 1,
#         #             then='open_balance',
#         #         ),
#         #         default=Value(0),
#         #         output_field=DecimalField(),
#         #     ),
#         # ),
#         #total_balance = Subquery(total.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')[:1]),
#         current=Subquery(current.filter(hr_customer=OuterRef('hr_customer')).values('open_balance')),
#         thirty=Subquery(thirty.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         sixty=Subquery(sixty.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         ninety=Subquery(ninety.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         onetwenty=Subquery(onetwenty.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         )
    
#     for x in individual_balances:
#         print(x)
    
#     # for x in individual_balances:
#     #     print(individual_balances)

#     context = {
#             'customers':customers,
#             'total_balance':total_balance,
#             'individual_balances':individual_balances,
#         }
#     return render(request, 'finance/reports/ar_aging.html', context)









# def ar_aging(request):
#     customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     current = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29)
#     thirty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59)
#     sixty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89)
#     ninety = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119)
#     onetwenty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120)

#     # Calculate the total balance
#     total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0

#     # Aggregate individual balances for each customer
#     individual_balances = customers.values('hr_customer').annotate(total_balance=Sum('open_balance'))

#     context = {
#             'customers':customers,
#             'total_balance':total_balance,
#             'individual_balances':individual_balances,
#         }
#     return render(request, 'finance/reports/ar_aging.html', context)







# @login_required
# def expanded_detail(request, id=None):
#     if not id:
#         id = request.GET.get('customers')
#         search = 0
#     else:
#         search = 1
#     customers = Customer.objects.all()
#     print(id)
#     if id:
#         aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
#         today = timezone.now()
#         for x in aging:
#             if not x.date_billed:
#                 x.date_billed = today
#             age = x.date_billed - today
#             age = abs((age).days)
#             print(type(age))
#             Workorder.objects.filter(pk=x.pk).update(aging = age)
        
#         customer = Customer.objects.get(id=id)
#         cust = customer.id
#         history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).order_by("-workorder")[:5]
#         workorder = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=1).exclude(quote=1).order_by("-workorder")[:25]
#         completed = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
#         quote = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
#         balance = Workorder.objects.filter(customer_id=customer).exclude(quote=1).aggregate(Sum('total_balance'))
#         current = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
#         thirty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
#         sixty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
#         ninety = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
#         onetwenty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
#         #current = list(current.values())[0]
#         #current = round(current, 2)


#         context = {
#             'workorders': workorder,
#             'completed': completed,
#             'quote': quote,
#             'cust': cust,
#             'customers':customers,
#             'customer': customer,
#             'history': history,
#             'balance': balance,
#             'current':current,
#             'thirty':thirty,
#             'sixty':sixty,
#             'ninety':ninety,
#             'onetwenty':onetwenty,
#         }
#         if search:
#             return render(request, "customers/search_detail.html", context)
#         else:
#             return render(request, "customers/partials/details.html", context)














    #         else:
    #             credit = workorder.total_balance















    #         total = workorder.total_balance
    #         date = timezone.now()
    #         credit = customer.credit
    #         if partial:
    #             partial = int(partial)
    #             if credit > partial:
    #                 open = workorder.open_balance
    #                 paid = workorder.amount_paid
    #                 if paid:
    #                     paid = paid + partial
    #                 else:
    #                     paid = partial
    #                 if paid > total:
    #                     partial = open
    #                     paid = total
    #                 open = open - partial
    #                 credit = credit - partial
    #                 Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, date_paid = date)
    #                 Customer.objects.filter(pk=cust).update(credit = credit)
    #                 return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    #             else:
    #                 return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    #         else:
    #             open = workorder.open_balance   
    #         if credit > open:
    #             Workorder.objects.filter(pk=pk).update(open_balance = 0, amount_paid = total, date_paid = date)
    #             credit = credit - open
    #             Customer.objects.filter(pk=cust).update(credit = credit)
    # return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})