#import os
#from io import BytesIO
#from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
###The following for weasyprint
from django.template.loader import get_template, render_to_string
from weasyprint import HTML, CSS
import tempfile
import datetime
from django.db.models import Sum
###To here
from xhtml2pdf import pisa
from django.views.generic import ListView
#from django.contrib.staticfiles import finders
from customers.models import Customer, Contact
from workorders.models import WorkorderItem, Workorder
from krueger.models import KruegerJobDetail

@login_required
def management(request):
    return render(request, 'pdf/management.html')

@login_required
def export_batch_statement_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + \
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

@login_required
def export_pdf(request, id):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + \
        str(datetime.datetime.now())+'.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'

    items = WorkorderItem.objects.filter(workorder=id)
    workorder = Workorder.objects.get(id=id)
    customer = Customer.objects.get(id=workorder.customer.id)
    try:
        contact = Contact.objects.get(id = workorder.contact)
    except:
        contact = ''
    #print(customer.company_name)
    date = datetime.date.today()
    subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
    tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
    total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
    l = len(items)
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

    context = {
        'items':items,
        'workorder':workorder,
        'customer':customer,
        'contact':contact,
        'date':date,
        'subtotal':subtotal,
        'tax':tax, 
        'total':total,
        'rows': rows
    }


    html_string=render_to_string('pdf/weasyprint/lk_invoice.html', context)
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
    items = KruegerJobDetail.objects.filter(workorder_item=id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=items.hr_workorder' + 'items.description.pdf'
    #remove inline to allow direct download
    #response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        
    response['Content-Transfer-Encoding'] = 'binary'


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