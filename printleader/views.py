from django.shortcuts import render
from django.db.models import Q
from .models import PrintleaderHistory
from django.contrib.auth.decorators import login_required

@login_required
def printleader_history(request):
    customer = PrintleaderHistory.objects.all().order_by('customer')
    unique_list = []
    list = []
    for x in customer:
        # check if exists in unique_list or not
        if x.customer not in list:
            unique_list.append(x)
            list.append(x.customer)
    q = request.GET.get('q')
    if q:
        workorders = PrintleaderHistory.objects.filter(
            Q(printleader_invoice__icontains=q) | Q(customer__icontains=q)
            ).distinct()
    else:
        workorders = ''
    context = {
        'workorders':workorders,
        'customers':unique_list,
    }
    return render (request, "printleader/printleader_history.html", context)

def printleader_history_detail(request):
    #Get all customers to create dropdown list
    customer = PrintleaderHistory.objects.all().order_by('customer')
    unique_list = []
    list = []
    for x in customer:
        # check if exists in unique_list or not
        if x.customer not in list:
            unique_list.append(x)
            list.append(x.customer)
    #Get workorders for selected customer
    id = request.GET.get('customers')
    x = PrintleaderHistory.objects.get(id=id)
    cust = x.printleader_customer_number
    name = x.customer
    #print(cust)
    workorders = PrintleaderHistory.objects.filter(printleader_customer_number = cust).order_by('-invoice_date')
    # print(workorders)
    # for x in workorders:
    #     print(x)
    context = {
        'name':name,
        'workorders':workorders,
        'customers':unique_list,
    }
    return render (request, "printleader/partials/printleader_history_detail.html", context)
