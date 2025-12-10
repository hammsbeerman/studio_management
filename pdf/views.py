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
from decimal import Decimal
from django.db.models import Sum
###To here
from xhtml2pdf import pisa
from django.views.generic import ListView
#from django.contrib.staticfiles import finders
from customers.models import Customer, Contact
from workorders.models import WorkorderItem, Workorder
from krueger.models import KruegerJobDetail, WideFormat
from finance.models import Krueger_Araging
from workorders.services.totals import compute_workorder_totals
from inventory.models import RetailWorkorderItem

@login_required
def invoice_pdf(request, id):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; attachment; filename=" + str(
        datetime.datetime.now()
    ) + ".pdf"
    # remove inline to allow direct download
    # response['Content-Disposition'] = 'attachment; filename=Expenses' + \
    response["Content-Transfer-Encoding"] = "binary"

    # Base workorder + items
    items = WorkorderItem.objects.filter(workorder=id)
    item_length = len(items)

    workorder = Workorder.objects.get(id=id)

    # 🔹 POS items attached to this workorder (queryset)
    pos_items_qs = RetailWorkorderItem.objects.filter(workorder=workorder)

    # 🔹 Compute a per-line total (qty × unit_price) for each POS item
    pos_items = []
    for p in pos_items_qs:
        # try both "quantity" and "qty" just in case
        qty = getattr(p, "quantity", None) or getattr(p, "qty", None) or 0
        unit_price = getattr(p, "unit_price", None) or 0

        try:
            qty = Decimal(str(qty))
        except Exception:
            qty = Decimal("0")

        try:
            unit_price = Decimal(str(unit_price))
        except Exception:
            unit_price = Decimal("0")

        p.invoice_total = qty * unit_price  # used in the template
        pos_items.append(p)

    # 🔹 POS origin sale (for "Created from POS sale #X" if you want it)
    pos_origin_sale = None
    first_pos = pos_items_qs.first()
    if first_pos is not None and getattr(first_pos, "sale_id", None):
        pos_origin_sale = first_pos.sale

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
    try:
        contact = Contact.objects.get(id=workorder.contact.id)
    except Exception:
        contact = ""

    # Legacy subtotal/tax/total based on WorkorderItem only
    subtotal = (
        WorkorderItem.objects.filter(workorder_id=id)
        .exclude(billable=0)
        .exclude(parent=1)
        .aggregate(Sum("absolute_price"))
    )
    tax = (
        WorkorderItem.objects.filter(workorder_id=id)
        .exclude(billable=0)
        .exclude(parent=1)
        .aggregate(Sum("tax_amount"))
    )
    total = (
        WorkorderItem.objects.filter(workorder_id=id)
        .exclude(billable=0)
        .exclude(parent=1)
        .aggregate(Sum("total_with_tax"))
    )

    l = len(items)

    # Paging + filler rows for layout
    if item_length > 15:
        items = WorkorderItem.objects.filter(workorder=id)[:15]
        items2 = WorkorderItem.objects.filter(workorder=id)[15:30]
        rows2 = ""
        n = 60
        for x in range(n):
            string = "<tr><td></td><td></td><td></td><td></td><td></td></tr>"
            rows2 += string
    else:
        items2 = ""
        rows2 = ""

    n = 40 - l
    rows = ""
    for x in range(n):
        string = "<tr><td></td><td></td><td></td><td></td><td></td></tr>"
        rows += string

    packingslip_rows = ""
    for x in range(n):
        string = "<tr><td></td><td></td><td></td><td></td></tr>"
        packingslip_rows += string

    if payment:
        total_bal = open_bal

    context = {
        "items": items,
        "items2": items2,
        "workorder": workorder,
        "customer": customer,
        "payment": payment,
        "contact": contact,
        "date": date,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "total_bal": total_bal,
        "rows": rows,
        "rows2": rows2,
        "packingslip_rows": packingslip_rows,
        # 🔹 POS-related
        "pos_items": pos_items,  # list with .invoice_total attached
        "pos_origin_sale": pos_origin_sale,
    }

    if workorder.internal_company == "LK Design":
        if item_length < 15:
            if workorder.quote == "0":
                html_string = render_to_string("pdf/weasyprint/lk_invoice.html", context)
            else:
                html_string = render_to_string("pdf/weasyprint/lk_quote.html", context)
        else:
            if workorder.quote == "0":
                html_string = render_to_string(
                    "pdf/weasyprint/lk_invoice_long.html", context
                )
            else:
                html_string = render_to_string(
                    "pdf/weasyprint/lk_quote_long.html", context
                )
    else:
        if workorder.quote == "0":
            html_string = render_to_string(
                "pdf/weasyprint/krueger_invoice.html", context
            )
        else:
            html_string = render_to_string(
                "pdf/weasyprint/krueger_quote.html", context
            )

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output = open(output.name, "rb")
        response.write(output.read())

    return response

@login_required
def workorder_invoice_pdf(request, id):
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
    """
    Customer statement PDF for a given customer, with optional company filters.

    ?company=Krueger+Printing&company=LK+Design&company=Office+Supplies

    Company logic (for header artwork):
        - Variant 1: Krueger and/or Office Supplies, but no LK
        - Variant 2: LK + (Krueger or Office Supplies)
        - Variant 3: LK only
    """
    # --- PDF response boilerplate ---
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        "inline; attachment; filename=" + str(datetime.datetime.now()) + ".pdf"
    )
    response["Content-Transfer-Encoding"] = "binary"

    # --- Company selection from querystring ---
    requested_companies = request.GET.getlist("company")
    valid_companies = ["Krueger Printing", "LK Design", "Office Supplies"]
    requested_companies = [c for c in requested_companies if c in valid_companies]

    # --- Base queryset: all open, non-void, non-quote workorders for this customer ---
    base_qs = (
        Workorder.objects.filter(customer=id)
        .exclude(billed=0)
        .exclude(paid_in_full=1)
        .exclude(quote=1)
        .exclude(void=1)
        .exclude(workorder_total=0)
        .order_by("workorder")
    )

    # Apply company filter if present; otherwise old behavior (exclude LK)
    if requested_companies:
        workorders = base_qs.filter(internal_company__in=requested_companies)
    else:
        workorders = base_qs.exclude(internal_company="LK Design")

    # --- Group workorders by company for the template ---

    lk_workorders = workorders.filter(
        internal_company="LK Design"
    ).order_by("date_billed", "workorder")

    kr_workorders = workorders.filter(
        internal_company="Krueger Printing"
    ).order_by("date_billed", "workorder")

    os_workorders = workorders.filter(
        internal_company="Office Supplies"
    ).order_by("date_billed", "workorder")

    lk_total = lk_workorders.aggregate(Sum("open_balance"))["open_balance__sum"] or Decimal("0.00")
    kr_total = kr_workorders.aggregate(Sum("open_balance"))["open_balance__sum"] or Decimal("0.00")
    os_total = os_workorders.aggregate(Sum("open_balance"))["open_balance__sum"] or Decimal("0.00")

    # If somehow nothing is left, just render an empty statement for this customer
    item_length = workorders.count()

    # --- Customer / contact info ---
    customer = Customer.objects.get(id=id)
    todays_date = timezone.now().date()

    try:
        contact = Contact.objects.get(id=customer.contact.id)
    except Exception:
        contact = ""

    # --- Company header variant logic (for artwork in template) ---
    # Companies actually present on this statement (after filters)
    companies_present = list(
        workorders.values_list("internal_company", flat=True).distinct()
    )

    selection = set(companies_present)

    lk = "LK Design" in selection
    kr = "Krueger Printing" in selection
    office = "Office Supplies" in selection

    # header_variant:
    #   1 = Krueger and/or Office (no LK)
    #   2 = LK + (Krueger or Office)
    #   3 = LK only
    if lk and not (kr or office):
        header_variant = 3
    elif lk and (kr or office):
        header_variant = 2
    else:
        header_variant = 1

    # --- Split items into first/second page & padding rows like the old logic ---

    if item_length > 15:
        items = workorders[:15]
        items2 = workorders[15:30]
        # 2nd-page padding rows (simple fixed number, like before)
        rows2 = ""
        for _ in range(60):
            rows2 += "<tr><td></td><td></td><td></td><td></td><td></td></tr>"
    else:
        items = workorders[:15]
        items2 = ""
        rows2 = ""

    # 1st-page padding rows to keep layout consistent
    n = max(0, 40 - item_length)
    rows = ""
    for _ in range(n):
        rows += "<tr><td></td><td></td><td></td><td></td><td></td></tr>"

    # --- Total balance for this customer / selection ---
    total_balance = workorders.aggregate(Sum("open_balance"))

    # --- Context into WeasyPrint template ---
    context = {
        "items": items,
        "items2": items2,
        "workorders": workorders,
        "lk_workorders": lk_workorders,
        "kr_workorders": kr_workorders,
        "os_workorders": os_workorders,
        "lk_total": lk_total,
        "kr_total": kr_total,
        "os_total": os_total,
        "customer": customer,
        "contact": contact,
        "date": todays_date,
        "todays_date": todays_date,
        "rows": rows,
        "rows2": rows2,
        "total_balance": total_balance,
        # NEW: drives header artwork and allows template to inspect companies
        "companies_present": companies_present,
        "header_variant": header_variant,
    }

    html_string = render_to_string(
        "pdf/weasyprint/statement.html", context
    )
    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output = open(output.name, "rb")
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
        
    item_length = len(workorders)
    print(item_length)
    
    ar = Krueger_Araging.objects.all()
    
    todays_date = timezone.now()
    try:
        contact = Contact.objects.get(id = customer.contact.id)
    except:
        contact = ''
    print(contact)
    #print(customer.company_name)
    date = datetime.date.today()
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


@login_required
def packing_slip(request, id):
    # --- Core objects --------------------------------------------------------
    workorder = get_object_or_404(Workorder, id=id)
    customer = get_object_or_404(Customer, id=workorder.customer_id)
    pos_items = RetailWorkorderItem.objects.filter(workorder=workorder)

    # WorkorderItems for this WO
    items_qs = WorkorderItem.objects.filter(workorder=workorder).order_by("id")
    item_length = items_qs.count()

    top_line_count = items_qs.filter(child=0).count()

    # Payment / balances
    payment = workorder.amount_paid
    open_bal = workorder.open_balance
    total_bal = workorder.total_balance

    # Date billed / billed flag
    date = workorder.date_billed
    if not date:
        workorder.date_billed = timezone.now()
        date = workorder.date_billed
        workorder.billed = 1
        workorder.save()

    # Contact (optional)
    try:
        contact = Contact.objects.get(id=workorder.contact_id)
    except Contact.DoesNotExist:
        contact = ""

    # --- Totals (same logic, just less repetition) ---------------------------
    chargeable = items_qs.exclude(billable=0).exclude(parent=1)

    subtotal = chargeable.aggregate(Sum("absolute_price"))
    tax = chargeable.aggregate(Sum("tax_amount"))
    total = chargeable.aggregate(Sum("total_with_tax"))

    # If there is a payment, use open balance as total balance
    if payment:
        total_bal = open_bal

    # --- Page splitting + filler rows ----------------------------------------
    # First page items
    if item_length > 15:
        items = items_qs[:15]
        items2 = items_qs[15:30]
        # second page filler
        rows2 = ""
        for _ in range(60):
            rows2 += "<tr><td></td><td></td><td></td><td></td><td></td></tr>"
    else:
        items = items_qs
        items2 = ""
        rows2 = ""

    # first page filler
    rows = ""
    n = max(0, 40 - item_length)
    for _ in range(n):
        rows += "<tr><td></td><td></td><td></td><td></td><td></td></tr>"

    # --- Office Supply flag to hide POS prices on packing slip --------------
    internal_company = (workorder.internal_company or "").strip()
    hide_pos_prices = internal_company in ["Office Supply", "Office Supplies"]

    # --- Context -------------------------------------------------------------
    context = {
        "items": items,
        "items2": items2,
        "workorder": workorder,
        "customer": customer,
        "payment": payment,
        "contact": contact,
        "date": date,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "total_bal": total_bal,
        "rows": rows,
        "rows2": rows2,
        "pos_items": pos_items,
        "hide_pos_prices": hide_pos_prices,  # <- use this in template
        "top_line_count": top_line_count, 
    }

    # --- Template selection (LK vs Krueger/Office Supply) --------------------
    if internal_company == "LK Design":
        if item_length < 15:
            if workorder.quote == "0":
                html_string = render_to_string("pdf/weasyprint/lk_packingslip.html", context)
            else:
                html_string = render_to_string("pdf/weasyprint/lk_quote.html", context)
        else:
            if workorder.quote == "0":
                html_string = render_to_string("pdf/weasyprint/lk_invoice_long.html", context)
            else:
                html_string = render_to_string("pdf/weasyprint/lk_quote_long.html", context)
    else:
        # Krueger + Office Supply share templates here
        if workorder.quote == "0":
            html_string = render_to_string("pdf/weasyprint/krueger_packingslip.html", context)
        else:
            html_string = render_to_string("pdf/weasyprint/krueger_quote.html", context)

    # --- Render PDF ----------------------------------------------------------
    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf_bytes = html.write_pdf()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Transfer-Encoding"] = "binary"
    # tweak filename if you like
    filename = f"packing-slip-wo-{workorder.id}.pdf"
    response["Content-Disposition"] = f'inline; attachment; filename="{filename}"'

    # You can stream directly; keeping temp file pattern is optional
    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(pdf_bytes)
        output.flush()
        with open(output.name, "rb") as f:
            response.write(f.read())

    return response