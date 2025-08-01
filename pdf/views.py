#import os
#from io import BytesIO
#from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
###The following for weasyprint
from django.template.loader import get_template, render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile
import datetime
from django.db.models import Sum
###To here
from xhtml2pdf import pisa
from django.views.generic import ListView
#from django.contrib.staticfiles import finders
from customers.models import Customer, Contact
from workorders.models import WorkorderItem, Workorder
from krueger.models import KruegerJobDetail, WideFormat
from finance.models import Krueger_Araging

@login_required
def invoice_pdf(request, id):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=' + \
        str(datetime.datetime.now())+'.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'

    items = WorkorderItem.objects.filter(workorder=id)
    item_length = len(items)

    
    workorder = Workorder.objects.get(id=id)
    payment = workorder.amount_paid
    open_bal = workorder.open_balance
    total_bal = workorder.total_balance
    date = workorder.date_billed
    if not workorder.date_billed:
        workorder.date_billed = timezone.now()
        date = workorder.date_billed
        workorder.billed = 1
        workorder.save()
    customer = Customer.objects.get(id=workorder.customer.id)
    print(workorder.contact)
    try:
        contact = Contact.objects.get(id = workorder.contact.id)
    except:
        contact = ''
    print(contact)
    #print(customer.company_name)
    #date = datetime.date.today()
    subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
    tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
    total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
    l = len(items)

    if item_length > 15:
        items = WorkorderItem.objects.filter(workorder=id)[:15]
        items2 = WorkorderItem.objects.filter(workorder=id)[15:30]
        rows2 = ''
        n = 60
        for x in range(n):
            string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
            #string = 'hello<br/>'
            #print('test')
            rows2 += string
    else:
        items2=''
        rows2 = ''
    print(l)
    n = 40 - l
    print(n)
    rows = ''
    for x in range(n):
        string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
        #string = 'hello<br/>'
        #print('test')
        rows += string
    #print(rows)

    if payment:
        total_bal = open_bal
    print('payment')
    print(payment)
    context = {
        'items':items,
        'items2':items2,
        'workorder':workorder,
        'customer':customer,
        'payment':payment,
        'contact':contact,
        'date':date,
        'subtotal':subtotal,
        'tax':tax, 
        'total':total,
        'total_bal':total_bal,
        'rows': rows,
        'rows2': rows2
    }

    if workorder.internal_company == 'LK Design':
        # i = len(items)
        # print('list length')
        # print(i)
        if item_length < 15:
            if workorder.quote == '0':
                html_string=render_to_string('pdf/weasyprint/lk_invoice.html', context)
            else:
                html_string=render_to_string('pdf/weasyprint/lk_quote.html', context)
        else:
            if workorder.quote == '0':
                html_string=render_to_string('pdf/weasyprint/lk_invoice_long.html', context)
            else:
                html_string=render_to_string('pdf/weasyprint/lk_quote_long.html', context)
    else:
        if workorder.quote == '0':
            html_string=render_to_string('pdf/weasyprint/krueger_invoice.html', context)
        else:
            html_string=render_to_string('pdf/weasyprint/krueger_quote.html', context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response

@login_required
def statement_pdf(request, id):
    print(id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=' + \
        str(datetime.datetime.now())+'.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'

    items = WorkorderItem.objects.filter(workorder=id)
    item_length = len(items)

    
    workorder = Workorder.objects.get(id=id)
    payment = workorder.amount_paid
    open_bal = workorder.open_balance
    total_bal = workorder.total_balance
    date = workorder.date_billed
    if not workorder.date_billed:
        workorder.date_billed = timezone.now()
        date = workorder.date_billed
        workorder.billed = 1
        workorder.save()
    customer = Customer.objects.get(id=workorder.customer.id)
    print(workorder.contact)
    try:
        contact = Contact.objects.get(id = workorder.contact.id)
    except:
        contact = ''
    print(contact)
    #print(customer.company_name)
    #date = datetime.date.today()
    subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
    tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
    total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
    l = len(items)

    if item_length > 15:
        items = WorkorderItem.objects.filter(workorder=id)[:15]
        items2 = WorkorderItem.objects.filter(workorder=id)[15:30]
        rows2 = ''
        n = 60
        for x in range(n):
            string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
            #string = 'hello<br/>'
            #print('test')
            rows2 += string
    else:
        items2=''
        rows2 = ''
    print(l)
    n = 40 - l
    print(n)
    rows = ''
    for x in range(n):
        string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
        #string = 'hello<br/>'
        #print('test')
        rows += string
    #print(rows)

    if payment:
        total_bal = open_bal
    print('payment')
    print(payment)
    context = {
        'items':items,
        'items2':items2,
        'workorder':workorder,
        'customer':customer,
        'payment':payment,
        'contact':contact,
        'date':date,
        'subtotal':subtotal,
        'tax':tax, 
        'total':total,
        'total_bal':total_bal,
        'rows': rows,
        'rows2': rows2
    }

    if workorder.internal_company == 'LK Design':
        # i = len(items)
        # print('list length')
        # print(i)
        if item_length < 15:
            if workorder.quote == '0':
                html_string=render_to_string('pdf/weasyprint/lk_invoice.html', context)
            else:
                html_string=render_to_string('pdf/weasyprint/lk_quote.html', context)
        else:
            if workorder.quote == '0':
                html_string=render_to_string('pdf/weasyprint/lk_invoice_long.html', context)
            else:
                html_string=render_to_string('pdf/weasyprint/lk_quote_long.html', context)
    else:
        if workorder.quote == '0':
            html_string=render_to_string('pdf/weasyprint/krueger_invoice.html', context)
        else:
            html_string=render_to_string('pdf/weasyprint/krueger_quote.html', context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response


@login_required
def lineitem_pdf(request, id):
    print(id)
    
    item = KruegerJobDetail.objects.get(workorder_item=id)
    if not item:
        item = WideFormat.objects.get(workorder_item=id)

    if item.description == 'None':
        item.description = ''
        
    if item.override_price:
        item.price_total = item.override_price

    print('id')
    print(item.workorder.id)

    workorder = Workorder.objects.get(pk=item.workorder.id)
    print(workorder)
    #workorder = 1


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=items.hr_workorder' + 'items.description.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'

    print(item)
    html_string=render_to_string('pdf/weasyprint/lineitem_pricing.html', {'item':item, 'workorder':workorder})
    html = HTML(string=html_string)

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response


@login_required
def ticket_pdf(request, id):
    print(id)
    
    item = KruegerJobDetail.objects.get(workorder_item=id)
    if not item:
        item = WideFormat.objects.get(workorder_item=id)

    if item.description == 'None':
        item.description = ''
        
    if item.override_price:
        item.price_total = item.override_price

    if item.mailmerge_qty == '0':
        item.mailmerge_qty = ''
    if item.step_white_compound_price == '0':
        item.step_white_compound_price = ''
    if item.step_NCR_compound_price == '0':
        item.step_NCR_compound_price = ''
    if item.perf_number_of_pieces == '0':
        item.perf_number_of_pieces = ''
    if item.number_price_to_number == '0':
        item.number_price_to_number = ''
    if item.step_insert_wrap_around_price == '0':
        item.step_insert_wrap_around_price = ''
    if item.step_drill_price == '0':
        item.step_drill_price = ''
    if item.staple_staples_per_piece == '0':
        item.staple_staples_per_piece = ''
    if item.fold_number_to_fold == '0':
        item.fold_number_to_fold = ''
    if item.tabs_number_of_pieces == '0':
        item.tabs_number_of_pieces = ''
    if item.step_bulk_mail_tray_sort_paperwork_price == '0':
        item.step_bulk_mail_tray_sort_paperwork_price = ''
    
    



    

    print('id')
    print(item.workorder.id)
    date = item.dateentered
    print(date)

    workorder = Workorder.objects.get(pk=item.workorder.id)
    print(workorder)
    #workorder = 1


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=items.hr_workorder' + 'items.description.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'

    print(item)
    
    html_string=render_to_string('pdf/weasyprint/jobticket.html', {'item':item, 'workorder':workorder, 'date':date})
    
    html = HTML(string=html_string)

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response


# @login_required
# def ticket_pdf(request, id):
#     return render(request, 'pdf/weasyprint/krueger_statement.html')






















#######################################   These aren't currently used




@login_required
def management(request):
    return render(request, 'pdf/management.html')

@login_required
def export_batch_statement_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=' + \
        str(datetime.datetime.now())+'.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
    #    str(datetime.datetime.now())+'.pdf'
    response['Content-Transfer-Encoding'] = 'binary'

    workorders = Workorder.objects.all()

    for x in workorders:
        print(x.id)
        items = WorkorderItem.objects.filter(workorder = x.id)
        #print(items.workorder_hr)

        html_string=render_to_string('pdf/weasyprint/pdf-output.html', {'items':items})
        html = HTML(string=html_string)

        result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response
























class CustomerListView(ListView):
    model = Customer
    template_name = 'pdf/customers/main.html'

@login_required
def customer_render_pdf_view(request, *args, **kwargs):
    pk = kwargs.get('pk')
    customer = get_object_or_404(Customer, pk=pk)
    template_path = 'pdf/customers/pdf2.html'
    context = {'customer': customer}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    ## 'attachment; filename="report.pdf"' is the part that downloads the pdf
    #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    ## If want to view pdf and not download, remove attachemnt as follows
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def render_pdf_view(request):
    template_path = 'pdf/pdf1.html'
    context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    ## 'attachment; filename="report.pdf"' is the part that downloads the pdf
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    ## If want to view pdf and not download, remove attachemnt as follows
    #response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def show_workorder_items(request):
    items = WorkorderItem.objects.all()
    context = {
        'items': items
    }
    return render(request, 'pdf/test2/showinfo.html', context)

# @login_required
#def pdf_report_create(request):
#    items = WorkorderItem.objects.all()
#    for item in items:
#       print('hi')
#       template_path = 'pdf/test2/pdfreport.html'
#       context = {'items': items}
#       # Create a Django response object, and specify content_type as pdf
#       response = HttpResponse(content_type='application/pdf')
#       ## 'attachment; filename="report.pdf"' is the part that downloads the pdf
#       response['Content-Disposition'] = 'attachment; filename='+item.description+'"report.pdf"'
#       ## If want to view pdf and not download, remove attachemnt as follows
#       #response['Content-Disposition'] = 'filename="report.pdf"'
#       # find the template and render it.
#       template = get_template(template_path)
#       html = template.render(context)

#       # create a pdf
#       pisa_status = pisa.CreatePDF(
#          html, dest=response)
#       # if error then show some funny view
#       if pisa_status.err:
#          return HttpResponse('We had some errors <pre>' + html + '</pre>')
#       return response
   
@login_required
def pdf_report_create(request): 
    items = WorkorderItem.objects.all()
    template_path = 'pdf/test2/pdfreport.html'
    context = {'items': items}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    ## 'attachment; filename="report.pdf"' is the part that downloads the pdf
    #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    ## If want to view pdf and not download, remove attachemnt as follows
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


##This one works
# @login_required
#def export_pdf(request):
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + \
#         str(datetime.datetime.now())+'.pdf'
#     #remove inline to allow direct download
#     #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
#     response['Content-Transfer-Encoding'] = 'binary'

#     items = WorkorderItem.objects.all()

#     html_string=render_to_string('pdf/weasyprint/pdf-output.html', {'items':items, 'total':0})
#     html = HTML(string=html_string)

#     result = html.write_pdf()

#     with tempfile.NamedTemporaryFile(delete=True) as output:
#         output.write(result)
#         output.flush()
#         #rb stands for read binary
#         output=open(output.name,'rb')
#         response.write(output.read())

#     return response

@login_required
def statement_pdf(request, id):
    print(id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=' + \
        str(datetime.datetime.now())+'.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'

    workorders = Workorder.objects.filter(customer=id).exclude(internal_company='LK Design').exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
    print(workorders)
    #payments = Payments.objects.filter(customer=pk).exclude(available = None).exclude(void = 1)
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    # total_balance=Sum('total_balance')
    # total_balance = workorders.filter().aggregate(Sum('open_balance'))

    # total_invoice = WorkorderItem.objects.filter(workorder_id=workorder).exclude(billable=0).exclude(parent=1).aggregate(
    #         sum=Sum('total_with_tax'),
    #         tax=Sum('tax_amount'),
    #         abs=Sum('absolute_price')
    #         )
    #credits = Customer.objects.get(pk=pk)
    #credits = credits.credit
    #print(credits)
    #customer = pk
    print(total_balance)

    # items = WorkorderItem.objects.filter(workorder=id)
    item_length = len(workorders)
    print(item_length)
    
    customer = Customer.objects.get(id=id)
    print(customer)

    # customers = Customer.objects.all()
    # ar = Krueger_Araging.objects.all()
    # for x in customers:
    #     id=x.id
    #     workorders = Workorder.objects.filter(customer=id).exclude(internal_company='LK Design').exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
    #     print(workorders)
    # payment = workorder.amount_paid
    # open_bal = workorder.open_balance
    # total_bal = workorder.total_balance
    # date = workorder.date_billed
    # if not workorder.date_billed:
    #     workorder.date_billed = timezone.now()
    #     date = workorder.date_billed
    #     workorder.billed = 1
    #     workorder.save()
    todays_date = timezone.now()
    # customer = Customer.objects.get(id=workorder.customer.id)
    # print(customer)
    # print(workorder.contact)
    try:
        contact = Contact.objects.get(id = customer.contact.id)
    except:
        contact = ''
    print(contact)
    #print(customer.company_name)
    date = datetime.date.today()
    # subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
    # tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
    # total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
    l = item_length

    if item_length > 15:
        items = Workorder.objects.filter(customer=id)[:15]
        items2 = Workorder.objects.filter(customer=id)[15:30]
        rows2 = ''
        n = 60
        for x in range(n):
            string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
            #string = 'hello<br/>'
            #print('test')
            rows2 += string
    else:
        items = WorkorderItem.objects.filter(workorder=id)[:15]
        items2=''
        rows2 = ''
    print(l)
    n = 40 - l
    print(n)
    rows = ''
    for x in range(n):
        string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
        #string = 'hello<br/>'
        #print('test')
        rows += string
    #print(rows)

    # if payment:
    #     total_bal = open_bal
    # print('payment')
    # print(payment)
    context = {
        'items':items,
        'items2':items2,
        # 'workorder':workorder,
        'workorders':workorders,
        'customer':customer,
        # 'payment':payment,
        'contact':contact,
        'date':date,
        'todays_date':todays_date,
        # 'subtotal':subtotal,
        # 'tax':tax, 
        # 'total':total,
        # 'total_bal':total_bal,
        'rows': rows,
        'rows2': rows2,
        # 'total_balance':total_balance
        'total_balance':total_balance,
        # 'customers':customers,

    }



    # if workorder.internal_company == 'LK Design':
    #     # i = len(items)
    #     # print('list length')
    #     # print(i)
    #     if item_length < 15:
    #         if workorder.quote == '0':
    #             html_string=render_to_string('pdf/weasyprint/lk_invoice.html', context)
    #         else:
    #             html_string=render_to_string('pdf/weasyprint/lk_quote.html', context)
    #     else:
    #         if workorder.quote == '0':
    #             html_string=render_to_string('pdf/weasyprint/lk_invoice_long.html', context)
    #         else:
    #             html_string=render_to_string('pdf/weasyprint/lk_quote_long.html', context)
    # else:
    #     if workorder.quote == '0':
    #         html_string=render_to_string('pdf/weasyprint/krueger_invoice.html', context)
        # else:
    html_string=render_to_string('pdf/weasyprint/krueger_statement.html', context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response

@login_required
def statement_pdf_bulk(request):
    # print(id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=' + \
        str(datetime.datetime.now())+'.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'


    #customers = Customer.objects.all()[:5]
    customers = Customer.objects.filter(id__in=Krueger_Araging.objects.values('customer')).order_by('company_name')
    
    customer_data = []
    for customer in customers:
        workorders = Workorder.objects.filter(customer=customer.id).exclude(internal_company='LK Design').exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
        print(workorders)

        total_open_balance = workorders.filter().aggregate(Sum('open_balance'))
        #total_open_balance = sum(w.open_balance for w in workorders)

        print(total_open_balance)

        if workorders.exists():
            customer_data.append({
                'customer': customer,
                'workorders': workorders,
                'total_open_balance': total_open_balance,
            })
        




    # workorders = Workorder.objects.filter(customer=id).exclude(internal_company='LK Design').exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
    # print(workorders)
    #payments = Payments.objects.filter(customer=pk).exclude(available = None).exclude(void = 1)
    # total_balance = workorders.filter().aggregate(Sum('open_balance'))
    # total_balance=Sum('total_balance')
    # total_balance = workorders.filter().aggregate(Sum('open_balance'))

    # total_invoice = WorkorderItem.objects.filter(workorder_id=workorder).exclude(billable=0).exclude(parent=1).aggregate(
    #         sum=Sum('total_with_tax'),
    #         tax=Sum('tax_amount'),
    #         abs=Sum('absolute_price')
    #         )
    #credits = Customer.objects.get(pk=pk)
    #credits = credits.credit
    #print(credits)
    #customer = pk
    #print(total_balance)

    # items = WorkorderItem.objects.filter(workorder=id)
    item_length = len(workorders)
    print(item_length)
    
    # customer = Customer.objects.get(id=id)
    # print(customer)

    
    ar = Krueger_Araging.objects.all()
    
    # payment = workorder.amount_paid
    # open_bal = workorder.open_balance
    # total_bal = workorder.total_balance
    # date = workorder.date_billed
    # if not workorder.date_billed:
    #     workorder.date_billed = timezone.now()
    #     date = workorder.date_billed
    #     workorder.billed = 1
    #     workorder.save()
    todays_date = timezone.now()
    # customer = Customer.objects.get(id=workorder.customer.id)
    # print(customer)
    # print(workorder.contact)
    try:
        contact = Contact.objects.get(id = customer.contact.id)
    except:
        contact = ''
    print(contact)
    #print(customer.company_name)
    date = datetime.date.today()
    # subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
    # tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
    # total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
    l = item_length

    if item_length > 15:
        items = Workorder.objects.filter(customer=id)[:15]
        items2 = Workorder.objects.filter(customer=id)[15:30]
        rows2 = ''
        n = 60
        for x in range(n):
            string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
            #string = 'hello<br/>'
            #print('test')
            rows2 += string
    else:
        # items = WorkorderItem.objects.filter(workorder=id)[:15]
        items2=''
        rows2 = ''
    print(l)
    n = 40 - l
    print(n)
    rows = ''
    for x in range(n):
        string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
        #string = 'hello<br/>'
        #print('test')
        rows += string
    #print(rows)

    # if payment:
    #     total_bal = open_bal
    # print('payment')
    # print(payment)
    context = {
        # 'items':items,
        # 'items2':items2,
        # 'workorder':workorder,
        'workorders':workorders,
        # 'customer':customer,
        # 'payment':payment,
        'contact':contact,
        'date':date,
        'todays_date':todays_date,
        # 'subtotal':subtotal,
        # 'tax':tax, 
        # 'total':total,
        # 'total_bal':total_bal,
        'rows': rows,
        'rows2': rows2,
        # 'total_balance':total_balance
        #'total_balance':total_balance,
        # 'customers':customers,
        'customer_data':customer_data,

    }



    # if workorder.internal_company == 'LK Design':
    #     # i = len(items)
    #     # print('list length')
    #     # print(i)
    #     if item_length < 15:
    #         if workorder.quote == '0':
    #             html_string=render_to_string('pdf/weasyprint/lk_invoice.html', context)
    #         else:
    #             html_string=render_to_string('pdf/weasyprint/lk_quote.html', context)
    #     else:
    #         if workorder.quote == '0':
    #             html_string=render_to_string('pdf/weasyprint/lk_invoice_long.html', context)
    #         else:
    #             html_string=render_to_string('pdf/weasyprint/lk_quote_long.html', context)
    # else:
    #     if workorder.quote == '0':
    #         html_string=render_to_string('pdf/weasyprint/krueger_invoice.html', context)
        # else:
    html_string=render_to_string('pdf/weasyprint/krueger_statement_bulk.html', context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        #rb stands for read binary
        output=open(output.name,'rb')
        response.write(output.read())

    return response

# workorders = Workorder.objects.filter(customer=pk).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(workorder_total=0).order_by('workorder')
#    payments = Payments.objects.filter(customer=pk).exclude(available = None).exclude(void = 1)
#    total_balance = workorders.filter().aggregate(Sum('open_balance'))
#    credits = Customer.objects.get(pk=pk)
#    credits = credits.credit
#    print(credits)
#    customer = pk
#    if msg:
#        message = "Please select a different payment"
#    else:
#        message = ''
#    context = {
#        'message':message,
#        'payments':payments,
#        'customer':customer,
#        'total_balance':total_balance,
#        'credit':credits,
#        'workorders':workorders,
#    }
#    return render(request, 'finance/reports/modals/open_invoices.html', context)


# @login_required
# def statement_pdf(request, id):
#     print(id)
    
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; attachment; filename=' + \
#         str(datetime.datetime.now())+'.pdf'
#     #remove inline to allow direct download
#     #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
#     response['Content-Transfer-Encoding'] = 'binary'

#     items = WorkorderItem.objects.filter(workorder=id)
#     item_length = len(items)

    
#     workorder = Workorder.objects.get(id=id)
#     payment = workorder.amount_paid
#     open_bal = workorder.open_balance
#     total_bal = workorder.total_balance
#     date = workorder.date_billed
#     if not workorder.date_billed:
#         workorder.date_billed = timezone.now()
#         date = workorder.date_billed
#         workorder.billed = 1
#         workorder.save()
#     customer = Customer.objects.get(id=workorder.customer.id)
#     print(workorder.contact)
#     try:
#         contact = Contact.objects.get(id = workorder.contact.id)
#     except:
#         contact = ''
#     print(contact)
#     #print(customer.company_name)
#     #date = datetime.date.today()
#     subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
#     tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
#     total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
#     l = len(items)

#     if item_length > 15:
#         items = WorkorderItem.objects.filter(workorder=id)[:15]
#         items2 = WorkorderItem.objects.filter(workorder=id)[15:30]
#         rows2 = ''
#         n = 60
#         for x in range(n):
#             string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
#             #string = 'hello<br/>'
#             #print('test')
#             rows2 += string
#     else:
#         items2=''
#         rows2 = ''
#     print(l)
#     n = 40 - l
#     print(n)
#     rows = ''
#     for x in range(n):
#         string = '<tr><td></td><td></td><td></td><td></td><td></td></tr>'
#         #string = 'hello<br/>'
#         #print('test')
#         rows += string
#     #print(rows)

#     if payment:
#         total_bal = open_bal
#     print('payment')
#     print(payment)
#     context = {
#         'items':items,
#         'items2':items2,
#         'workorder':workorder,
#         'customer':customer,
#         'payment':payment,
#         'contact':contact,
#         'date':date,
#         'subtotal':subtotal,
#         'tax':tax, 
#         'total':total,
#         'total_bal':total_bal,
#         'rows': rows,
#         'rows2': rows2
#     }

#     if workorder.internal_company == 'LK Design':
#         # i = len(items)
#         # print('list length')
#         # print(i)
#         if item_length < 15:
#             if workorder.quote == '0':
#                 html_string=render_to_string('pdf/weasyprint/lk_invoice.html', context)
#             else:
#                 html_string=render_to_string('pdf/weasyprint/lk_quote.html', context)
#         else:
#             if workorder.quote == '0':
#                 html_string=render_to_string('pdf/weasyprint/lk_invoice_long.html', context)
#             else:
#                 html_string=render_to_string('pdf/weasyprint/lk_quote_long.html', context)
#     else:
#         if workorder.quote == '0':
#             html_string=render_to_string('pdf/weasyprint/krueger_invoice.html', context)
#         else:
#             html_string=render_to_string('pdf/weasyprint/krueger_quote.html', context)

#     html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))

#     result = html.write_pdf()

#     with tempfile.NamedTemporaryFile(delete=True) as output:
#         output.write(result)
#         output.flush()
#         #rb stands for read binary
#         output=open(output.name,'rb')
#         response.write(output.read())

#     return response