from django.shortcuts import render
from django.db.models import Q
from .models import PrintleaderHistory, PrintleaderARINVODA
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
    #Search function not written out yet
    #q = request.GET.get('q')
    # if q:
    #     workorders = PrintleaderHistory.objects.filter(
    #         Q(printleader_invoice__icontains=q) | Q(customer__icontains=q)
    #         ).distinct()
    # else:
    #     workorders = ''
    context = {
        #'workorders':workorders,
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
    #print(list)
    #print(unique_list)
    #Get workorders for selected customer
    id = request.GET.get('customers')
    x = PrintleaderHistory.objects.get(id=id)
    cust = x.printleader_customer_number
    name = x.customer
    #print(cust)
    workorders = PrintleaderHistory.objects.filter(printleader_customer_number = cust).order_by('-invoice_date')
    work = []
    for workorder in workorders:
        details = PrintleaderARINVODA.objects.filter(InvoiceNum = x.printleader_invoice)
        work.append({
            'workorder': workorder.printleader_invoice,
             'detail': [detail.Jobname for detail in details]
        })




    # work = []
    # for x in workorders:
    #     print(x)
    #     work.append([])
    #     invoice = x.printleader_invoice
    #     details = PrintleaderARINVODA.objects.filter(InvoiceNum = invoice)
    #     print(work)
    #     print('i')
    #     print(details)
    #     #for y in details:
    #     for j in details:
    #         print('hello')
    #         print(work[x])
    #         work[x].append(4)
    #         print(work[x])
    # print(work)

    # print('space')    
    # matrix = []
    # for i in range(6):
    #     # Append an empty sublist inside the list
    #     matrix.append([])
    #     print(matrix)
    #     for j in range(5):
    #         matrix[i].append(j)
    # print(matrix)

    #print(workorders)

    # for x in workorders:
    #     print('i')
    #     work.append([])
    #     details = PrintleaderARINVODA.objects.filter()
    # print(details)

    # for x in workorders:
    #     description = PrintleaderARINVODA.objects.filter(InvoiceNum = x.printleader_invoice)
    #     print(description)
    # print(workorders)
    # for x in workorders:
    #     print(x)
    context = {
        'work':work,
        'name':name,
        'workorders':workorders,
        'customers':unique_list,
    }
    return render (request, "printleader/partials/printleader_history_detail.html", context)

def job_details(request):
    num = 23390
    workorder = PrintleaderHistory.objects.get(printleader_invoice=num)
    print(workorder.id)

    detail = '23614'
    print(detail)
    obj = PrintleaderARINVODA.objects.filter(InvoiceNum = detail)
    for x in obj:
        print('ok')
        print(x.Jobname)
    print('end')
    for x in workorder:
        try:
            detail = PrintleaderARINVODA.objects.get(InvoiceNum = x.printleader_invoice)
            print(detail.InvoiceNum)
        except:
            detail = None
            #print('No match')
        detail = 23614
        if detail is not None:
            #print(detail.InvoiceNum)
            #print(detail.Lineno)
            #invoice = detail.InvoiceNum
            #invoice = 23614
            #print(invoice)
            obj = PrintleaderARINVODA.objects.filter(InvoiceNum = detail)
            for x in obj:
                print(x.Jobname)
                #print('hello')
            #print(obj)
            #print('duh')
            #for x in obj:
            #    print(x.Jobname)
            # for x in invoice:
            #     obj = PrintleaderARINVODA.objects.get(InvoiceNum = x)
                # print(obj.Jobname)
            # #detail = PrintleaderARINVODA.objects.filter(InvoiceNum = x.printleader_invoice)
            # for y in detail:
            #     print(detail.Lineno)
            #     invoice = x.printleader_invoice
            #     customer = x.customer
            #     customer_number = x.printleader_customer_number
            #     job_name = detail.Jobname
            #     print(invoice)
            #     print(customer)
            #     print(customer_number)
            #     print(job_name)
        else:
            pass
            
    return render (request, "printleader/printleader_history.html")
