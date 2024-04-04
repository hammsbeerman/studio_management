from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, Count, Min, Sum, Subquery, Case, When, Value, DecimalField, OuterRef
from django.db.models import Q
from django.utils import timezone
import logging
from .models import AccountsPayable, DailySales
from .forms import AccountsPayableForm, DailySalesForm
from customers.models import Customer
from workorders.models import Workorder
from .forms import PaymentForm
from controls.models import PaymentType

logger = logging.getLogger(__file__)

def finance_main(request):
    return render(request, 'finance/main.html')

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
            workorders = Workorder.objects.filter(customer_id = customer).exclude(total_balance=0).exclude(paid_in_full=1).order_by("-workorder")
        except:
            workorders = 'No Workorders Available'
    print(workorders)
    context = {
        'customer':selected_customer,
        'customers':customers,
        'workorders':workorders,
    }
    return render(request, "finance/AR/partials/workorder_list.html", context)

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
    if request.method == "POST":
            customer = request.POST.get('customer')
            print(customer)
            check = request.POST.get('check_number')
            giftcard = request.POST.get('giftcard_number')
            refund = request.POST.get('refunded_invoice_number')
            form = PaymentForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.check_number = check
                print(obj.check_number)
                obj.giftcard_number = giftcard
                obj.refunded_invoice_number = refund
                obj.save()
                print(customer)
                cust = Customer.objects.get(id=customer)
                try:
                    credit = cust.credit + obj.amount
                except: 
                    credit = obj.amount
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
                return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = PaymentForm
    context = {
        'paymenttype':paymenttype,
        'form': form,
    }
    return render(request, 'finance/AR/modals/recieve_payment.html', context)

@login_required
def unrecieve_payment(request):
    paymenttype = PaymentType.objects.all()
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
    }
    return render(request, 'finance/AR/modals/unrecieve_payment.html', context)

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

def apply_payment(request):
    if request.method == "POST":
            cust = request.POST.get('customer')
            pk = request.POST.get('pk')
            customer = Customer.objects.get(id=cust)
            workorder = Workorder.objects.get(id=pk)
            partial = request.POST.get('partial_payment')
            total = workorder.total_balance
            date_billed = workorder.date_billed
            if not date_billed:
                date_billed = timezone.now()
            date = timezone.now()
            days_to_pay = date - date_billed
            days_to_pay = abs((days_to_pay).days)
            avg_days = Workorder.objects.filter(customer_id=cust).exclude(days_to_pay=0).aggregate(avg=Avg('days_to_pay'))
            avg_days = list(avg_days.values())[0]
            print(avg_days)
            print(days_to_pay)
            if not avg_days:
                avg_days = 0
            credit = customer.credit
            if partial:
                print('partial')
                print(partial)
                full_payment = 0
                partial = int(partial)
                if credit > partial:
                    open = workorder.open_balance
                    paid = workorder.amount_paid
                    if paid:
                        paid = paid + partial
                    else:
                        paid = partial
                    if paid > total:
                        partial = open
                        paid = total
                        full_payment = 1
                    open = open - partial
                    credit = credit - partial
                    print(full_payment)
                    Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, paid_in_full = full_payment, date_paid = date)
                    #open_balance = Workorder.objects.filter(customer_id=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
                    open_balance = Workorder.objects.filter(customer_id=cust).exclude(completed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
                    open_balance = list(open_balance.values())[0]
                    open_balance = round(open_balance, 2)
                    print(open_balance)
                    Customer.objects.filter(pk=cust).update(credit = credit, open_balance = open_balance)
                    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
                else:
                    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
            else:
                open = workorder.open_balance 
            if credit >= open:
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
                Customer.objects.filter(pk=cust).update(credit = credit, avg_days_to_pay = avg_days, open_balance = open_balance)
    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})

def unapply_payment(request):
    if request.method == "POST":
        cust = request.POST.get('customer')
        pk = request.POST.get('pk')
        customer = Customer.objects.get(id=cust)
        workorder = Workorder.objects.get(id=pk)
        print(customer)
        print(workorder)
        print(pk)
        # partial = request.POST.get('p')
        # g = request.POST.get('g')
        # k = request.POST.get('k')
        # date = ''
        # print(g)
        # print(k)
        # print(pk)
        # print(cust)
        # print(workorder)
        # print(partial)
        # if partial:
        #     credit = partial
        #     total = workorder.total_balance
        #     open = workorder.open_balance
        #     paid = workorder.amount_paid
        #     if open:
        #         open = open + partial
        #     else:
        #         open = partial
        #     paid = total - open
        #     Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, date_paid = date)
        # else:
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
                



def add_bill_payable(request):
    form = AccountsPayableForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added...")
                return redirect('finance:add_bill_payable')
        return render(request, 'finance/AP/add_ap.html', {'form':form})
    else:
        messages.success(request, "You must be logged in")
        return redirect('home')
    
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
    
def view_daily_sales(request):
    sales_list = DailySales.objects.all()
    return render(request, 'finance/reports/view_sales.html',
        {'sales_list': sales_list})

def view_bills_payable(request):
    bills_list = AccountsPayable.objects.all()
    return render(request, 'finance/AP/view_bills.html',
        {'bill_list': bills_list})



def ar_aging(request):
    customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
    current = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer').annotate(current_balance=Sum('open_balance'))
    thirty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).values('hr_customer').annotate(thirty=Sum('open_balance'))
    sixty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).values('hr_customer').annotate(sixty=Sum('open_balance'))
    ninety = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).values('hr_customer').annotate(ninety=Sum('open_balance'))
    onetwenty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).values('hr_customer').annotate(onetwenty=Sum('open_balance'))
    total = customers.all().values('hr_customer').annotate(total_balance=Sum('open_balance'))

    #total_balance = Workorder.objects.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
    total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0

    # Aggregate individual balances for each customer
    individual_balances = Workorder.objects.values('hr_customer').annotate(
        #total_balance=Sum('open_balance'),
        total_balance=Subquery(total.filter(hr_customer=models.OuterRef('hr_customer')).values('total_balance')[:1]),
        current=Subquery(current.filter(hr_customer=models.OuterRef('hr_customer')).values('current_balance')[:1]),
        #current=Subquery(current),
        thirty=Subquery(thirty.filter(hr_customer=models.OuterRef('hr_customer')).values('thirty')[:1]),
        sixty=Subquery(sixty.filter(hr_customer=models.OuterRef('hr_customer')).values('sixty')[:1]),
        ninety=Subquery(ninety.filter(hr_customer=models.OuterRef('hr_customer')).values('ninety')[:1]),
        onetwenty=Subquery(onetwenty.filter(hr_customer=models.OuterRef('hr_customer')).values('onetwenty')[:1]),
        )
    
    for x in individual_balances:
        print(x)

    context = {
            'customers':customers,
            'total_balance':total_balance,
            'individual_balances':individual_balances,
        }
    return render(request, 'finance/reports/ar_aging.html', context)








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







@login_required
def expanded_detail(request, id=None):
    if not id:
        id = request.GET.get('customers')
        search = 0
    else:
        search = 1
    customers = Customer.objects.all()
    print(id)
    if id:
        aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
        today = timezone.now()
        for x in aging:
            if not x.date_billed:
                x.date_billed = today
            age = x.date_billed - today
            age = abs((age).days)
            print(type(age))
            Workorder.objects.filter(pk=x.pk).update(aging = age)
        
        customer = Customer.objects.get(id=id)
        cust = customer.id
        history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).order_by("-workorder")[:5]
        workorder = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=1).exclude(quote=1).order_by("-workorder")[:25]
        completed = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
        quote = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
        balance = Workorder.objects.filter(customer_id=customer).exclude(quote=1).aggregate(Sum('total_balance'))
        current = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
        thirty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
        sixty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
        ninety = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
        onetwenty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
        #current = list(current.values())[0]
        #current = round(current, 2)


        context = {
            'workorders': workorder,
            'completed': completed,
            'quote': quote,
            'cust': cust,
            'customers':customers,
            'customer': customer,
            'history': history,
            'balance': balance,
            'current':current,
            'thirty':thirty,
            'sixty':sixty,
            'ninety':ninety,
            'onetwenty':onetwenty,
        }
        if search:
            return render(request, "customers/search_detail.html", context)
        else:
            return render(request, "customers/partials/details.html", context)














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