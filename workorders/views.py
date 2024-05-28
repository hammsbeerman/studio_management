from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count, Min, Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
from django.contrib import messages
from customers.models import Customer, Contact
from controls.models import Numbering, Category, SubCategory, SetPriceCategory, SetPriceItemPrice
from .models import Workorder, DesignType, WorkorderItem
from .forms import WorkorderForm, WorkorderNewItemForm, WorkorderItemForm, DesignItemForm, NoteForm, WorkorderNoteForm, CustomItemForm, ParentItemForm, PostageItemForm, JobStatusForm, ItemDetailForm
from krueger.forms import KruegerJobDetailForm, WideFormatDetailForm
from krueger.models import KruegerJobDetail, WideFormat
from inventory.forms import OrderOutForm, SetPriceForm, PhotographyForm
from inventory.models import OrderOut, SetPrice, Photography
from pricesheet.forms import WideFormatForm
from accounts.models import Profile

@login_required
def create_base(request):
    #newcustomerform = CustomerForm(request.POST or None)
    customer = Customer.objects.all()
    # workorder = Numbering.objects.get(name='Workorder Number')
    # workorder = int(workorder.value)
    # inc = int('1')
    # workordernum = workorder + inc
    #workorder = Numbering.objects.WorkorderNum
    #print(workorder)
            # workorder = workorder += 1
            # print(workorder)
    categories = Category.objects.all().distinct().exclude(active=0).order_by('name')
    context = {
        'customers': customer,
        #'newcustomerform': newcustomerform,
        'form': WorkorderForm(),
        #'workordernum': workordernum,
        'categories':categories,
        #'messages':messages,
    }
    if request.method == "POST":
        print('hi')
        form = WorkorderForm(request.POST)
        #print(form.internal_company)
        print(form.errors)
        quote = request.POST.get('quote')
        form.fields['quote'].choices = [(quote, quote)]
        if not form.is_valid():
            print(form.errors)
            print('error')
            messages.error(request, "Please correct the errors below and resubmit.")
            return render(request, context)
        else:# form.is_valid():
            form.instance.customer_id = request.POST.get('customer')
            quote = request.POST.get('quote')
            cust = form.instance.customer_id
            select = 'Select Customer'
            if cust == select:
                message = "Please select a customer"
                context = {
                        'customers': customer,
                        'message': message,
                        'form': form,}
                print(cust)
                print(select)
                return render(request, "workorders/create.html", context)
            hrcust = Customer.objects.get(id=cust)
            hrcust.updated=datetime.now
            hrcust.save()
            print(hrcust.tax_exempt)
            if hrcust.tax_exempt:
                print('tax exempt')
                form.instance.tax_exempt = 1
            form.instance.po_number = hrcust.po_number
            hrcust = hrcust.company_name
            form.instance.hr_customer = hrcust
            print(cust)
            print(hrcust)
            #
            form.instance.contact_id = request.POST.get('contacts')
            cont = form.instance.contact_id
            if cont:
                hrcont = Contact.objects.get(id=cont)
                hrcont = hrcont.fname
                form.instance.hr_contact = hrcont
            ##Increase workorder numbering
            print('quote')
            print(quote)
            if quote == '1':
                print('quote')
                print('test')
                n = Numbering.objects.get(name='Quote Number')
                form.instance.quote_number = n.value
                form.instance.workorder = n.value
                form.instance.workorder_status_id = 9
                print(form.instance.workorder_status) 
                print(n.value)
            else: 
                print('workorder')
                n = Numbering.objects.get(name='Workorder Number')
                form.instance.workorder = n.value
                form.instance.workorder_status_id = 1
            workorder = n.value
            inc = int('1')
            n.value = n.value + inc
            print(n.value)
            ## End of numbering
            print('hello')
            form.save()
            context = {
                'id': n.value,
            }
            n.save()
            #messages.success(request, 'workorder added.')
            return redirect("workorders:overview", id=workorder)
            #return render(request, "workorders/overview.html", context)
        # else:
        #     for error in form.errors:
        #         messages.error(request, WorkorderForm.errors[error])
        #         return redirect(request.path)
    
    return render(request, "workorders/create.html", context)

@login_required
def overview(request, id=None):
    print('id')
    print(id)
    workorder = Workorder.objects.get(workorder=id)
    #if not workorder:
    #    workorder = request.GET.get('workorder')
    customer = Customer.objects.get(id=workorder.customer_id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    print(id)
    history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).exclude(void=1).order_by("-workorder")[:5]
    workid = workorder.id
    categories = Category.objects.all().distinct().exclude(active=0).order_by('name')
    #total = decimal.Decimal(total.total_price__sum)
    changecustomer = customer.id
    changeworkorder = workorder.id
    context = {
            'workid': workid,
            'workorder': workorder,
            'customer': customer,
            'contact': contact,
            'history': history,
            'categories':categories,
            'changecustomer':changecustomer,
            'changeworkorder':changeworkorder
        }
    return render(request, "workorders/overview.html", context)

@login_required
def history_overview(request, id):
    workorder = Workorder.objects.get(workorder=id)
    customer = Customer.objects.get(id=workorder.customer_id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    history = Workorder.objects.filter(customer_id=customer).order_by("-workorder")[:10].exclude(workorder=1111)
    context = {
            'workorder': workorder,
            'customer': customer,
            'contact': contact,
            'history': history,
        }
    return render(request, "workorders/partials/history_overview.html", context)

@login_required
def dashboard(request, id=None):
    visitor = request.user.id
    items = WorkorderItem.objects.filter(assigned_user_id = visitor).exclude(completed=1).order_by("-workorder")
    company = Profile.objects.get(user_id = visitor)
    company = company.primary_company
    #print(company.primary_company)
    #status = JobStatus.objects.all()
    context = {
        'company':company,
        'items':items,
        #'status':status,
    }
    return render(request, "workorders/list.html", context)

@login_required
def workorder_list(request):
    workorder = Workorder.objects.all().exclude(workorder=1111).exclude(orderout_waiting=1).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    orderout = Workorder.objects.all().exclude(workorder=1111).exclude(orderout_waiting=0).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    completed = Workorder.objects.all().exclude(workorder=1111).exclude(completed=0).exclude(quote=1).exclude(void=1).order_by("-date_completed")[:20]
    quote = Workorder.objects.all().exclude(workorder=1111).exclude(quote=0).exclude(void=1).order_by("-workorder")
    context = {
        'workorders': workorder,
        'completed': completed,
        'orderout': orderout,
        'quote': quote,

    }
    return render(request, 'workorders/partials/list_sm_order.html', context)

@login_required
def workorder_k_list(request):
    workorder = Workorder.objects.all().filter(internal_company="Krueger Printing").exclude(workorder=1111).exclude(orderout_waiting=1).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    orderout = Workorder.objects.all().filter(internal_company="Krueger Printing").exclude(workorder=1111).exclude(orderout_waiting=0).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    completed = Workorder.objects.all().filter(internal_company="Krueger Printing").exclude(workorder=1111).exclude(completed=0).exclude(quote=1).exclude(void=1).order_by("-date_completed")[:20]
    quote = Workorder.objects.all().filter(internal_company="Krueger Printing").exclude(workorder=1111).exclude(quote=0).exclude(void=1).order_by("-workorder")
    context = {
        'workorders': workorder,
        'completed': completed,
        'orderout': orderout,
        'quote': quote,

    }
    return render(request, 'workorders/partials/list_k_order.html', context)

@login_required
def workorder_lk_list(request):
    workorder = Workorder.objects.all().filter(internal_company="LK Design").exclude(workorder=1111).exclude(orderout_waiting=1).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    orderout = Workorder.objects.all().filter(internal_company="LK Design").exclude(workorder=1111).exclude(orderout_waiting=0).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    completed = Workorder.objects.all().filter(internal_company="LK Design").exclude(workorder=1111).exclude(completed=0).exclude(quote=1).exclude(void=1).order_by("-date_completed")[:20]
    quote = Workorder.objects.all().filter(internal_company="LK Design").exclude(workorder=1111).exclude(quote=0).exclude(void=1).order_by("-workorder")
    context = {
        'workorders': workorder,
        'completed': completed,
        'orderout': orderout,
        'quote': quote,

    }
    return render(request, 'workorders/partials/list_lk_order.html', context)

@login_required
def workorder_kos_list(request):
    workorder = Workorder.objects.all().filter(internal_company="Office Supplies").exclude(workorder=1111).exclude(orderout_waiting=1).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    orderout = Workorder.objects.all().filter(internal_company="Office Supplies").exclude(workorder=1111).exclude(orderout_waiting=0).exclude(completed=1).exclude(quote=1).exclude(void=1).order_by("-workorder")
    completed = Workorder.objects.all().filter(internal_company="Office Supplies").exclude(workorder=1111).exclude(completed=0).exclude(quote=1).exclude(void=1).order_by("-date_completed")[:20]
    quote = Workorder.objects.all().filter(internal_company="Office Supplies").exclude(workorder=1111).exclude(quote=0).exclude(void=1).order_by("-workorder")
    context = {
        'workorders': workorder,
        'completed': completed,
        'orderout': orderout,
        'quote': quote,

    }
    return render(request, 'workorders/partials/list_kos_order.html', context)

@login_required
def quote_list(request):
    workorder = Workorder.objects.all().exclude(workorder=1111).exclude(quote=0).exclude(void=1)
    context = {
        'workorders': workorder,
    }
    return render(request, 'workorders/quotes.html', context)

@login_required
def edit_workorder(request):
    workorder = request.GET.get('workorder')
    try:
        void = Workorder.objects.get(id=workorder)
    except:
        void = ''
    #void = void.void
    print(workorder)
    #customer = request.GET.get('customer')
    if request.method == "POST":
        workorder_num = request.POST.get("workorder")
        print(workorder_num)
        customer = request.POST.get('customer')
        customer = Customer.objects.get(pk=customer)
        print(customer)
        print(customer.company_name)
        obj = get_object_or_404(Workorder, pk=workorder_num)
        #obj = (Contact, pk=contact_num)
        form = WorkorderForm(request.POST, instance=obj)
        if form.is_valid():
                print('valid')
                form.save()
                Workorder.objects.filter(pk=workorder_num).update(hr_customer = customer.company_name)
                return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderInfoChanged'})
    else:
        obj = get_object_or_404(Workorder, id=workorder)
        form = WorkorderForm(instance=obj)
        context = {
            'void': void,
            'form': form,
            'workorder': workorder
        }
    return render(request, 'workorders/modals/edit_workorder.html', context)

@login_required
def workorder_info(request):
    if request.htmx:
        workorder = request.GET.get('workorder')
        print(workorder)
        workorder = Workorder.objects.get(pk=workorder)
        context = { 'workorder': workorder,}
        return render(request, 'workorders/partials/workorder_info.html', context)
    
##########Add Items
@login_required
def add_item(request, parent_id):
    print(parent_id)
    categories = Category.objects.all().distinct().exclude(active=0).order_by('name')
    if request.method == "POST":
        form = WorkorderNewItemForm(request.POST)
        desc = request.POST.get('description')
        cat = request.POST.get('item_category')
        subcat = request.POST.get('subcategory')
        print('Category')
        print(cat)
        print('sub')
        print(subcat)
        print(desc)
        if not desc:
            message = "Please enter a description"
            print(message)
            context = {
                'form':form,
                'categories': categories,
                'message':message
            }
            return render(request, 'workorders/modals/new_item_form.html', context)
        if form.is_valid():
            #subcategory = request.POST.get('item_subcategory')
            #print('subcategory')
            #print(subcategory)
            obj = form.save(commit=False)
            obj.item_subcategory_id = subcat
            #obj = request.POST.get
            parent = Workorder.objects.get(pk=parent_id)
            ('parent id')
            print(parent_id)
            #Add workorder to form since it wasn't displayed
            obj.workorder_id = parent_id
            print('parent')
            print(parent.workorder)
            obj.tax_exempt = parent.customer.tax_exempt
            obj.internal_company = parent.internal_company
            print(parent.customer.tax_exempt)
            print(parent.customer.customer_number)
            print('up')
            #obj.last_item_price = '78964'
            obj.workorder_hr = parent.workorder
            obj.assigned_user_id = request.user.id
            #obj.test_user_id = request.user.profile.id
            obj.job_status_id = 1
            #obj.item_subcategory = subcategory
            obj.save()
            print('objpk')
            print(obj.pk)
            print(cat)
            if cat=='13':
                obj = WorkorderItem.objects.get(id=obj.pk)
                obj.parent_item = obj.pk
                print(obj.parent_item)
                obj.save()
            print(obj.pk)
            print(parent.customer)
            print(parent.customer_id)
            print('parent id')
            print(parent.id)
            #print(parent.category)
            loadform = Category.objects.get(id=cat)
            print(loadform.customform)
            print(parent.workorder)
            if loadform.customform is True:
                #loadform = Category.objects.get(id=category)
                modelname = globals()[loadform.modelname]
                formname = globals()[loadform.formname]
                if formname == DesignItemForm or formname == CustomItemForm or formname == ParentItemForm or formname == PostageItemForm:
                    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
                #form = formname(request.POST, instance=item)
                print(modelname)
                detailbase = modelname(workorder_id = parent.id, hr_workorder=parent.workorder, workorder_item =obj.pk, internal_company = parent.internal_company,
                                          customer_id=parent.customer_id, hr_customer=parent.hr_customer, category = cat, description = desc,)
            else:
                print('not custom')
                detailbase = KruegerJobDetail(workorder_id = parent.id, hr_workorder=parent.workorder, workorder_item =obj.pk, internal_company = parent.internal_company,
                                          customer_id=parent.customer_id, hr_customer=parent.hr_customer, category = cat, subcategory = subcat, description = desc,
                                          )
            detailbase.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    else:
        form = WorkorderNewItemForm()
        categories = Category.objects.all().distinct().exclude(active=0).order_by('name')
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'workorders/modals/new_item_form.html', context)

@login_required
def workorder_item_list(request, id=None):
    #print(id)
    if not request.htmx:
        raise Http404
    try:
        #print(id)
        #id=1
        #obj = get_object_or_404(Workorder, id=id,)
        #qs = Workorder.objects.all()
        print('hello')
        print(id)
        completed = Workorder.objects.get(id=id)
        obj = WorkorderItem.objects.filter(workorder_id=id)
        #category = Category.objects.filter(id=obj.item_category.id)
        #print(category.name)
        #print(obj.item_category_id.name)
        subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).exclude(tax_exempt=1).aggregate(Sum('absolute_price'))
        subtotal_exempt = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).exclude(tax_exempt=0).aggregate(Sum('absolute_price'))
        tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('tax_amount'))
        total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('total_with_tax'))
        print('Abs tax')
        #print(abs_tax)
        subtotal_aggregate = list(subtotal.values())[0]
        subtotal_exempt_aggregate = list(subtotal_exempt.values())[0]
        if subtotal_aggregate:
            print(subtotal_aggregate)
            tax_percent = Decimal.from_float(.055)
            tax_amount = Decimal.from_float(1.055)
            abs_tax = subtotal_aggregate * tax_percent
            abs_tax = round(abs_tax, 2)
            print(subtotal_aggregate)
            print(tax_percent)
            print(abs_tax)
        else:
            abs_tax = 0
        if not subtotal_aggregate:
            subtotal_aggregate = 0
        if not subtotal_exempt_aggregate:
            subtotal_exempt_aggregate = 0
        if not abs_tax:
            abs_tax = 0
        subtotal = subtotal_aggregate + subtotal_exempt_aggregate
        total = subtotal_aggregate + subtotal_exempt_aggregate + abs_tax
        #abs_tax = round(abs_tax, 2)
        #override_total = WorkorderItem.objects.filter(workorder_id=id).exclude(override_price__isnull=True).aggregate(Sum('override_price'))
        print('total')
        print(total)
    except:
        obj = None
    if obj is  None:
        print('broken')
        return HttpResponse("Not found.")
    test = 'notes'
    context = {
        "test": test,
        "items": obj,
        "subtotal":subtotal,
        #"tax":tax,
        "abs_tax":abs_tax,
        "total": total,
    }
    print(completed.completed)
    if completed.completed == 1:
        return render(request, "workorders/partials/item_list_completed.html", context)
    return render(request, "workorders/partials/item_list.html", context) 

@login_required
def workorder_total(request, id=None):
    #print(id)
    if not request.htmx:
        raise Http404
    try:
        print(id)
        obj = WorkorderItem.objects.filter(workorder_id=id)

    except:
        obj = None
    if obj is  None:
        return HttpResponse("Not found.")
    context = {
        "items": obj
    }
    return render(request, "workorders/partials/item_list.html", context) 



@login_required
def edit_print_item(request):
    pass




@login_required
def edit_modal_item(request, pk, cat):
    item = get_object_or_404(WorkorderItem, pk=pk)
    line = request.POST.get('item')
    category = cat
    inventory = item.item_category.inventory_category
    print(inventory)
    if request.method == "POST":
        print('hello')
        category = request.POST.get('cat')
        print('category')
        print(category)
        ####
        #Get form to load from category
        loadform = Category.objects.get(id=category)
        formname = globals()[loadform.formname]
        modelname = globals()[loadform.modelname]
        form = formname(request.POST, instance=item)
        #formname = globals()[loadform.formname]
        #form = OrderOutForm(request.POST, instance=item)
        #print(formname)
        ####
        #form = DesignItemForm(request.POST, instance=item)
        obj = form.save(commit=False)
        #form.instance.item_category = category
        if form.is_valid():
            if loadform.customform is True:
                print('true')
                ################################### Need to change this to global modal and form if antother is added
                newobj = get_object_or_404(modelname, workorder_item=pk)
                print(newobj.id)
                itemform = formname(request.POST, instance=newobj)
                if itemform.is_valid():
                    itemform.save()
                    unit_price = request.POST.get('unit_price')
                    print(unit_price)
                    lineitem = modelname.objects.get(id=itemform.instance.pk)
                    lineitem.edited = 1
                    lineitem.unit_price = unit_price
                    lineitem.save()
                    # print('pk')
                    # print(itemform.instance.pk)
                    #itemform.save(commit=False)
                    #itemform.edited = 1  
                else:
                    print(form.errors)
            print(form.instance.id)
            print('valid')
            form.save()
            print(obj.quantity)
            qty = obj.quantity
            unit_price=obj.unit_price
            print('unitprice')
            print(unit_price)
            total=0
            if qty and unit_price:
                total = qty * unit_price
            print(qty)
            print(unit_price)
            print(total)
            lineitem = WorkorderItem.objects.get(id=line)
            lineitem.quantity = qty
            lineitem.unit_price = unit_price
            lineitem.total_price = total
            lineitem.pricesheet_modified = 1
            lineitem.save()
            # print(line)
            # lineitem = WorkorderItem.objects.get(id=line)
            # lineitem = WorkorderItem(quantity=obj.quantity, unit_price=obj.unit_price, total_price=total, item_category_id=category)
            # lineitem.update()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
        else:
            print(form.errors)
    print(category)
    obj = Category.objects.get(id=category)  
    print('object name')      
    print(obj.name)
    ####
    #Get form to load from category
    loadform = Category.objects.get(id=cat)
    formname = globals()[loadform.formname]
    #formname = loadform.formname
    modelname = globals()[loadform.modelname]
    if loadform.customform is True:
        if loadform.setprice is True:
            item = get_object_or_404(modelname, workorder_item=pk)
            price_ea = item.unit_price
            form = formname(instance=item)
            context = {
            'pk':pk,
            'form': form,
            'item': item,
            'obj': obj,
            'cat': category,
            'price_ea': price_ea,
            }
            return render(request, 'workorders/modals/setprice_item_form.html', context)
        item = get_object_or_404(modelname, workorder_item=pk)
        price_ea = item.unit_price
    form = formname(instance=item)
    ####
    #form = DesignItemForm(instance=item)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
        'price_ea': price_ea,
    }
    return render(request, 'workorders/modals/design_item_form.html', context)


# @login_required
# def edit_order_out_item(request, pk, cat):
#     pass


@login_required
def edit_design_item(request, pk, cat):
    item = get_object_or_404(WorkorderItem, pk=pk)
    #line = request.POST.get('item')
    category = cat
    if request.method == "POST":
        form = DesignItemForm(request.POST, instance=item)
        obj = form.save(commit=False)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        qty = obj.quantity
        unit_price=obj.unit_price
        total=0
        if qty and unit_price:
            total = qty * unit_price
        lineitem = WorkorderItem.objects.get(id=pk)
        lineitem.quantity = qty
        lineitem.unit_price = unit_price
        lineitem.total_price = total
        lineitem.pricesheet_modified = 1
        lineitem.absolute_price = total
        tax_percent = Decimal.from_float(.055)
        tax = Decimal.from_float(1.055)
        if lineitem.tax_exempt == 1:
            lineitem.tax_amount = 0
            lineitem.total_with_tax = lineitem.absolute_price
        else:
            rounded_tax = lineitem.absolute_price * tax
            rounded_tax = round(rounded_tax, 2)
            lineitem.tax_amount = rounded_tax - lineitem.absolute_price
            lineitem.total_with_tax = rounded_tax
        lineitem.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    print(category)
    obj = Category.objects.get(id=category)  
    print('object name')      
    print(obj.name)
    #formname == DesignItemForm:
    item = get_object_or_404(WorkorderItem, pk=pk)
    price_ea = item.unit_price
    form = DesignItemForm(instance=item)
    ####
    #form = DesignItemForm(instance=item)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
        'price_ea': price_ea,
    }
    return render(request, 'workorders/modals/design_item_form.html', context)

@login_required
def edit_postage_item(request, pk, cat):
    item = get_object_or_404(WorkorderItem, pk=pk)
    #line = request.POST.get('item')
    category = cat
    if request.method == "POST":
        form = PostageItemForm(request.POST, instance=item)
        obj = form.save(commit=False)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        qty = obj.quantity
        unit_price=obj.unit_price
        total=0
        if qty and unit_price:
            total = qty * unit_price
        lineitem = WorkorderItem.objects.get(id=pk)
        lineitem.quantity = qty
        lineitem.unit_price = unit_price
        lineitem.total_price = total
        lineitem.pricesheet_modified = 1
        lineitem.absolute_price = total
        tax_percent = Decimal.from_float(.055)
        tax = Decimal.from_float(1.055)
        if lineitem.tax_exempt == 1:
            lineitem.tax_amount = 0
            lineitem.total_with_tax = lineitem.absolute_price
        else:
            rounded_tax = lineitem.absolute_price * tax
            rounded_tax = round(rounded_tax, 2)
            lineitem.tax_amount = rounded_tax - lineitem.absolute_price
            lineitem.total_with_tax = rounded_tax
        lineitem.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    print(category)
    obj = Category.objects.get(id=category)  
    print('object name')      
    print(obj.name)
    #formname == DesignItemForm:
    item = get_object_or_404(WorkorderItem, pk=pk)
    price_ea = item.unit_price
    form = PostageItemForm(instance=item)
    ####
    #form = DesignItemForm(instance=item)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
        'price_ea': price_ea,
    }
    return render(request, 'workorders/modals/postage_item_form.html', context)

@login_required
def edit_custom_item(request, pk, cat):
    item = get_object_or_404(WorkorderItem, pk=pk)
    #line = request.POST.get('item')
    category = cat
    inventory = item.item_category.inventory_category
    print(inventory)
    if request.method == "POST":
        form = CustomItemForm(request.POST, instance=item)
        obj = form.save(commit=False)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        qty = obj.quantity
        unit_price=obj.unit_price
        total=0
        if qty and unit_price:
            total = qty * unit_price
        lineitem = WorkorderItem.objects.get(id=pk)
        lineitem.quantity = qty
        lineitem.unit_price = unit_price
        lineitem.total_price = total
        lineitem.pricesheet_modified = 1
        lineitem.absolute_price = total
        tax_percent = Decimal.from_float(.055)
        tax = Decimal.from_float(1.055)
        if lineitem.tax_exempt == 1:
            lineitem.tax_amount = 0
            lineitem.total_with_tax = lineitem.absolute_price
        else:
            rounded_tax = lineitem.absolute_price * tax
            rounded_tax = round(rounded_tax, 2)
            lineitem.tax_amount = rounded_tax - lineitem.absolute_price
            lineitem.total_with_tax = rounded_tax
        lineitem.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    print(category)
    obj = Category.objects.get(id=category)  
    print('object name')      
    print(obj.name)
    #formname == DesignItemForm:
    item = get_object_or_404(WorkorderItem, pk=pk)
    price_ea = item.unit_price
    form = CustomItemForm(instance=item)
    ####
    #form = DesignItemForm(instance=item)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
        'price_ea': price_ea,
    }
    return render(request, 'workorders/modals/custom_item_form.html', context)

@login_required
def edit_orderout_item(request, pk, cat):
    print('pk')
    print(pk)
    item = get_object_or_404(OrderOut, workorder_item=pk)
    #line = request.POST.get('item')
    #print('line')
    #print(line)
    category = cat
    if request.method == "POST":
        form = OrderOutForm(request.POST, instance=item)
        obj = form.save(commit=False)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        qty = obj.quantity
        total = obj.total_price
        override = obj.override_price
        if override:
                print(type(override))
                override = (float(override))
                override = Decimal.from_float(override)
                temp_total = override
                #print(type(obj.quantity))
                try:
                    price_ea = temp_total / qty
                except:
                    price_ea = 0
        else:
            temp_total = total
        try: 
            unit_price = temp_total / qty
        except:
            unit_price = 0
        lineitem = WorkorderItem.objects.get(id=pk)
        lineitem.description = obj.description
        lineitem.quantity = qty
        lineitem.unit_price = unit_price
        lineitem.total_price = total
        lineitem.override_price = override
        lineitem.pricesheet_modified = 1
        lineitem.absolute_price = temp_total
        tax_percent = Decimal.from_float(.055)
        tax = Decimal.from_float(1.055)
        if lineitem.tax_exempt == 1:
            lineitem.tax_amount = 0
            lineitem.total_with_tax = lineitem.absolute_price
        else:
            rounded_tax = lineitem.absolute_price * tax
            rounded_tax = round(rounded_tax, 2)
            lineitem.tax_amount = rounded_tax - lineitem.absolute_price
            lineitem.total_with_tax = rounded_tax
        if lineitem.notes:
            notes = lineitem.notes
        else:
            notes = ''
        if lineitem.last_item_order:
            last_order = lineitem.last_item_order
        else:
            last_order = ''
        if lineitem.last_item_price:
            last_price = lineitem.last_item_order
        else:
            last_price = ''
        lineitem.save()
        orderoutitem = OrderOut.objects.get(workorder_item=pk)
        orderoutitem.last_item_order = last_order
        orderoutitem.last_order_price = last_price
        orderoutitem.notes = notes
        orderoutitem.unit_price = unit_price
        orderoutitem.edited = 1
        orderoutitem.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    print(category)
    obj = Category.objects.get(id=category)  
    print('object name')      
    print(obj.name)
    #formname == DesignItemForm:
    item = get_object_or_404(OrderOut, workorder_item=pk)
    price_ea = item.unit_price
    form = OrderOutForm(instance=item)
    ####
    #form = DesignItemForm(instance=item)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
        'price_ea': price_ea,
    }
    return render(request, 'workorders/modals/order_out_form.html', context)

@login_required
def edit_set_price_item(request, pk, cat):
    pass
    print('pk')
    print(pk)
    item = get_object_or_404(SetPrice, workorder_item=pk)
    print(item.setprice_category)
    print(item.setprice_item)
    print('above')
    try:
        setprice = SetPriceCategory.objects.get(id=item.setprice_category)
        setprice_selected = setprice.name
        print(setprice_selected)
        try:
            obj_item = SetPriceItemPrice.objects.filter(name=item.setprice_category)
            try:
                selected = SetPriceItemPrice.objects.get(id=item.setprice_item)
            except:
                selected = ''
                pass
                print(item)
                print(obj)
        except:
            obj_item = ''
            selected = ''
            pass
    except:
        selected = ''
        obj_item = ''
        setprice_selected = ''
    setprice_category = SetPriceCategory.objects.all()
    category = cat
    if request.method == "POST":
        form = SetPriceForm(request.POST, instance=item)
        obj = form.save(commit=False)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        #setpric = request.POST.get('unit_price')
        qty = obj.total_pieces
        print(qty)
        qty = (float(qty))
        qty = Decimal.from_float(qty)
        total = obj.total_price
        override = obj.override_price
        #setprice_category = obj.setprice_item
        setprice_category = request.POST.get('setprice_category')
        setprice_item = request.POST.get('setprice_item')

       # print(setprice)
        #setprice_category = get_object_or_404(SetPriceCategory, id=setprice)
        # setprice_item = SetPriceCategory.objects.get(id=setprice)
        # print('name')
        # print(setprice_item.name)
        
        #print('setprice')
        #print(setprice_item.name)
        #print(setprice_item.description)
        if override:
                print(type(override))
                override = (float(override))
                override = Decimal.from_float(override)
                temp_total = override
                #print(type(obj.quantity))
                price_ea = temp_total / qty
        else:
            temp_total = total
        unit_price = temp_total / qty
        lineitem = WorkorderItem.objects.get(id=pk)
        lineitem.quantity = qty
        lineitem.setprice_category_id = setprice_category
        lineitem.setprice_item_id = setprice_item
        lineitem.description = obj.description
        lineitem.unit_price = unit_price
        lineitem.internal_company = obj.internal_company
        lineitem.total_price = total
        lineitem.override_price = override
        lineitem.pricesheet_modified = 1
        lineitem.absolute_price = temp_total
        tax_percent = Decimal.from_float(.055)
        tax = Decimal.from_float(1.055)
        if lineitem.tax_exempt == 1:
            lineitem.tax_amount = 0
            lineitem.total_with_tax = lineitem.absolute_price
        else:
            rounded_tax = lineitem.absolute_price * tax
            rounded_tax = round(rounded_tax, 2)
            lineitem.tax_amount = rounded_tax - lineitem.absolute_price
            lineitem.total_with_tax = rounded_tax
        if lineitem.notes:
            notes = lineitem.notes
        else:
            notes = ''
        if lineitem.last_item_order:
            last_order = lineitem.last_item_order
        else:
            last_order = ''
        if lineitem.last_item_price:
            last_price = lineitem.last_item_order
        else:
            last_price = ''
        lineitem.save()
        setpricecategory = SetPrice.objects.get(workorder_item=pk)
        setpricecategory.last_item_order = last_order
        setpricecategory.last_item_price = last_price
        setpricecategory.notes = notes
        setpricecategory.unit_price = unit_price
        setpricecategory.edited = 1
        setpricecategory.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    print(category)
    #obj = Category.objects.get(id=category)  
    #print('object name')      
    #print(obj.name)
    #formname == DesignItemForm:
    item = get_object_or_404(SetPrice, workorder_item=pk)
    price_ea = item.unit_price
    form = SetPriceForm(instance=item)
    ####
    #form = DesignItemForm(instance=item)
    print(setprice_selected)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'obj': obj_item,
        'selected':selected,
        'cat': category,
        'price_ea': price_ea,
        'setprice_category':setprice_category,
        #'setprice_item': setprice_item,
        'setprice_selected':setprice_selected,
    }
    print(pk)
    print(pk)
    return render(request, 'workorders/modals/set_price_form.html', context)


@login_required
def edit_parent_item(request, pk, cat, workorder):
    wo = workorder
    pass
    print('pk')
    print(pk)
    item = WorkorderItem.objects.filter(workorder = wo, parent_item__isnull=True).exclude(item_category=13) | WorkorderItem.objects.filter(parent_item = pk).exclude(item_category=13)
    show_on_wo = WorkorderItem.objects.get(pk=pk)
    if request.method == "POST":
        formerchildren = WorkorderItem.objects.filter(workorder = wo, parent_item = pk)
        formerchildren.update(child=0)
        formerchildren.update(parent_item=None)
        #item.update(child=0)
        childs = request.POST.getlist('child')
        qty = request.POST.get('quantity')
        desc = request.POST.get('description')
        show = request.POST.get('showonwo')
        if show:
            show = 1
        else:
            show = 0
        print(childs)
        ap = 0
        ta = 0
        twt = 0
        for c in childs:
            x = WorkorderItem.objects.get(pk=c)
            print('pk')
            print(pk)
            x.child = 1
            x.parent_item = pk
            x.save()
            try:
                ap = ap + x.absolute_price
            except:
                pass
            try:
                ta = ta + x.tax_amount
            except:
                pass
            try:
                twt = twt + x.total_with_tax
            except:
                pass
            print(twt)
        print(twt)
        parent = WorkorderItem.objects.get(pk=pk)
        if qty:
            #parent.quantity = qty
            print(ap)
            print(qty)
            dec_ap = (float(ap))
            dec_ap = Decimal.from_float(dec_ap)
            dec_qty = (float(qty))
            dec_qty = Decimal.from_float(dec_qty)
            print(dec_ap)
            print(dec_qty)
            parent.unit_price = dec_ap / dec_qty
        parent.show_qty_on_wo = show
        parent.quantity = dec_qty
        parent.description = desc
        parent.absolute_price = ap
        parent.tax_amount = ta
        parent.total_with_tax = twt
        parent.parent_item = pk
        parent.parent = 1
        parent.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    formitem = get_object_or_404(WorkorderItem, pk=pk)
    form = ParentItemForm(instance=formitem)
    context = {
        'pk':pk,
        'form': form,
        'item': item,
        'show_on_wo': show_on_wo,
        # 'obj': obj_item,
        # 'selected':selected,
        # 'cat': category,
        # 'price_ea': price_ea,
        # 'setprice_category':setprice_category,
        #'setprice_item': setprice_item,
        #'setprice_selected':setprice_selected,
    }
    return render(request, 'workorders/modals/parent_item_form.html', context)

        

















# def edit_design_item(request, pk, cat):
#     item = get_object_or_404(WorkorderItem, pk=pk)
#     #line = request.POST.get('item')
#     category = cat
#     if request.method == "POST":
#         print('hello')
#         category = request.POST.get('cat')
#         print('category')
#         print(category)
#         ####
#         #Get form to load from category
#         # loadform = Category.objects.get(id=category)
#         # formname = globals()[loadform.formname]
#         # modelname = globals()[loadform.modelname]
#         form = DesignItemForm(request.POST, instance=item)
#         obj = form.save(commit=False)
#         #form.instance.item_category = category
#         if form.is_valid():
#             newobj = get_object_or_404(WorkorderItem, pk=pk)
#             print('newobj')
#             print(newobj.id)
#             itemform = DesignItemForm(request.POST, instance=newobj)
#             if itemform.is_valid():
#                 itemform.save()
#                 unit_price = request.POST.get('unit_price')
#                 print(unit_price)
#                 lineitem = WorkorderItem.objects.get(id=itemform.instance.pk)
#                 #lineitem.edited = 1
#                 lineitem.unit_price = unit_price
#                 lineitem.save()
#             else:
#                 print(form.errors)
#             qty = obj.quantity
#             unit_price=obj.unit_price
#             print('unitprice')
#             print(unit_price)
#             total=0
#             if qty and unit_price:
#                 total = qty * unit_price
#             lineitem = WorkorderItem.objects.get(id=pk)
#             lineitem.quantity = qty
#             lineitem.unit_price = unit_price
#             lineitem.total_price = total
#             lineitem.pricesheet_modified = 1
#             lineitem.save()
#             return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
#    


#@ require_POST
@login_required
def remove_workorder_item(request, pk):
    if request.method == "POST":
        nonmodal = request.POST.get('nonmodal')
        item = get_object_or_404(WorkorderItem, pk=pk)
        print(item.workorder_hr)
        workorder = item.workorder_hr
        groupitem = WorkorderItem.objects.filter(parent_item=pk)
        try:
            groupitem.update(parent_item=None, child=0)
        except:
            pass
        item.delete()
        if nonmodal == '1':
            return redirect("workorders:overview", id=workorder)
        else:
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    item = get_object_or_404(WorkorderItem, pk=pk)
    if item.setprice_category:
        subitem = get_object_or_404(SetPrice, workorder_item=pk)
        subitem.delete()
    groupitem = WorkorderItem.objects.filter(parent_item=pk)
    groupitem.update(parent_item=None, child=0)
    item.delete()
    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})


@login_required
def copy_workorder_item(request, pk, workorder=None):
    #Copy line item to current workorder
    if workorder:
        print(pk)
        obj = WorkorderItem.objects.get(pk=pk)
        obj.pk = None
        print('asdakldmakldamsl')
        obj.added_to_parent = 0
        obj.parent = 0
        obj.parent_item = None
        obj.child = 0
        obj.void = 0
        obj.void_memo = None
        obj.completed = 0
        obj.job_status_id = 1
        obj.save()
        #print(obj.pk)
        #print(pk)
        #Copy coresponding kruegerjobdetail item
        try: 
            objdetail = KruegerJobDetail.objects.get(workorder_item=pk)
            print(objdetail)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except Exception as e:
            print(1)
            print("The error is:", e)
        try: 
            objdetail = WideFormat.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except Exception as e:
            print(2)
            print("The error is:", e)
        try:
            objdetail = OrderOut.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.total_price
            objdetail.save()
        except Exception as e:
            print(3)
            print("The error is:", e)
        try:
            objdetail = SetPrice.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.total_price
            objdetail.save()
        except Exception as e:
            print(4)
            print("The error is:", e)
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    #Copy line item to different workorder
    #This section is called from copy item modal
    if request.method == "POST":
        #Workorder to copy to
        workorder = request.POST.get('workorder')
        #Get info from workorder being copied to
        new = Workorder.objects.get(workorder=workorder)
        # print('Workorder copying to')
        # print(new.pk)
        # print('Current workorder item pk')
        # print(pk)
        #copy data from existing line item
        obj = WorkorderItem.objects.get(pk=pk)
        obj.pk = None
        last_workorder = obj.workorder_hr
        obj.workorder_hr = workorder
        obj.workorder_id = new.pk
        #Fill in missing data in new line item
        obj.last_item_order = last_workorder
        if obj.absolute_price:
            obj.last_item_price = obj.absolute_price
        else:
            obj.last_item_price = obj.total_price
        # print(obj.last_item_order)
        obj.save()
        #Copy corresponding kruegerjobdetail to new object
        try:
            objdetail = KruegerJobDetail.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.workorder_id = new.pk
            objdetail.hr_workorder = new.workorder
            objdetail.last_item_order = last_workorder
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
        try: 
            objdetail = WideFormat.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.price_total
            objdetail.save()  
        except Exception as e:
            print("The error is:", e)      
        try:
            objdetail = OrderOut.objects.get(workorder_item=pk)
            print('hello')
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.total_price
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
        try:
            objdetail = SetPrice.objects.get(workorder_item=pk)
            objdetail.pk = None
            print(objdetail.description)
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.total_price
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    obj = WorkorderItem.objects.get(pk=pk)
    workorders = Workorder.objects.all().exclude(workorder=1111).exclude(billed=1).order_by("-workorder")
    context = {
        'obj': obj,
        'workorders': workorders,
        #'workorder': workorder
    }
    return render(request, 'workorders/modals/copy_item.html', context)

#This is for the duplicate workorder button
@login_required
def copy_workorder(request, id=None):
    print (id)
    #Get data from current workorder
    obj = Workorder.objects.get(id=id)
    lastworkorder = obj.workorder
    n = Numbering.objects.get(pk=1)
    #Update settings for new workorder
    obj.workorder = n.value
    obj.quote_number = ''
    obj.completed = 0
    obj.original_order = lastworkorder
    obj.billed = 0
    obj.date_billed = None
    obj.open_balance = obj.workorder_total
    obj.total_balance = obj.workorder_total
    obj.paid_in_full = 0
    obj.days_to_pay = ''
    obj.aging = None
    obj.void = 0
    obj.workorder_status_id = 1
    obj.lk_workorder = None
    obj.printleader_workorder = None
    obj.kos_workorder = None
    #Increment workorder number
    newworkorder = obj.workorder
    #Update numbering table
    inc = int('1')
    n.value = n.value + inc
    n.save()
    #save workorder with new workorder number
    obj.pk=None
    #obj.
    obj.save()
    new_workorder_id=obj.pk
    print(id)
    print(newworkorder)
    #print(new_id)
    workorder_item = WorkorderItem.objects.filter(workorder_id=id)
    for item in workorder_item:
        #print('workorder item id')
        #print(item.id)
        oldid = item.id
        workorder = item.workorder_hr
        price = item.total_price
        #jobitem = item.pk
        print(workorder)
        print(price)
        item.workorder_id=new_workorder_id
        item.pk=None
        item.workorder_hr=newworkorder
        item.last_item_order=workorder
        item.void = 0
        item.void_memo = None
        item.completed = 0
        item.job_status_id = 1
        if item.absolute_price:
            item.last_item_price = item.absolute_price
        else:
            item.last_item_price=price            
        item.save()
        #Copy kruegerjobdetail for each item
        print(item.pk)
        try:
            objdetail = KruegerJobDetail.objects.get(workorder_item=oldid)
            objdetail.pk = None
            print('New workorder')
            print(new_workorder_id)
            objdetail.workorder_item = item.pk
            objdetail.workorder_id = new_workorder_id
            objdetail.hr_workorder = newworkorder
            objdetail.last_item_order = lastworkorder
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
        try: 
            objdetail = WideFormat.objects.get(workorder_item=oldid)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
        try:
            objdetail = OrderOut.objects.get(workorder_item=oldid)
            print('hello')
            objdetail.workorder_item = item.pk
            objdetail.workorder_id = new_workorder_id
            objdetail.pk = None
            objdetail.hr_workorder = newworkorder
            objdetail.last_item_order = lastworkorder
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.total_price
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
        try:
            objdetail = SetPrice.objects.get(workorder_item=oldid)
            objdetail.workorder_item = item.pk
            objdetail.workorder_id = new_workorder_id
            objdetail.pk = None
            print(objdetail.description)
            objdetail.hr_workorder = newworkorder
            objdetail.last_item_order = lastworkorder
            if objdetail.override_price:
                objdetail.last_item_price = objdetail.override_price
            else:
                objdetail.last_item_price = objdetail.total_price
            objdetail.save()
        except Exception as e:
            print("The error is:", e)
    print(newworkorder)
    workorder_parent = WorkorderItem.objects.filter(workorder_hr=newworkorder, parent=1)
    for item in workorder_parent:
        parent = item.id
        oldparent = item.parent_item
        print(item.created)
        print(item.id)
        print('oldparent')
        print(item.parent_item)
        print(oldparent)
        print('parent')
        print(parent)
        children = WorkorderItem.objects.filter(workorder_hr=newworkorder, parent_item=oldparent)
        for c in children:
            c.parent_item = item.id
            print(c.parent_item)
            print(item.id)
            c.save()
    return redirect('workorders:overview', id=newworkorder)

@login_required
def subcategory(request):
    cat = request.GET.get('item_category')
    print(cat)
    obj = SubCategory.objects.filter(category_id=cat)
    context = {
        'obj':obj
    }
    return render(request, 'workorders/modals/subcategory.html', context) 

@login_required
def tax(request, tax, id):
    tax_percent = Decimal.from_float(.055)
    tax_sum = Decimal.from_float(1.055)
    if tax == 'False':
        print('False')
        lineitem = WorkorderItem.objects.get(id=id)
        lineitem.tax_exempt = 1
        lineitem.tax_amount = 0
        lineitem.total_with_tax = lineitem.absolute_price
        lineitem.save() 
        context = {
            'tax':True,
            'id':id,
        }
    else:
        print('True')
        lineitem = WorkorderItem.objects.get(id=id)
        lineitem.tax_exempt = 0
        if lineitem.absolute_price is not None:
            rounded_tax = lineitem.absolute_price * tax_sum
            rounded_tax = round(rounded_tax, 2)
            lineitem.tax_amount = rounded_tax - lineitem.absolute_price
            lineitem.total_with_tax = rounded_tax
        lineitem.save()
        context = {
            'tax':False,
            'id':id,
        }
    return render(request, 'workorders/partials/tax.html', context)

@login_required
def notes(request, pk=None):
    item = get_object_or_404(WorkorderItem, pk=pk)
    if request.method == "POST":
        id = request.POST.get('id')
        print(id)
        item = get_object_or_404(WorkorderItem, pk=id)
        form = NoteForm(request.POST, instance=item)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = NoteForm(instance=item)
    context = {
        #'notes':notes,
        'form':form,
        'pk': pk,
    }
    return render(request, 'workorders/modals/notes.html', context) 


@login_required
def workorder_notes(request, pk=None):
    item = get_object_or_404(Workorder, pk=pk)
    if request.method == "POST":
        id = request.POST.get('id')
        print(id)
        item = get_object_or_404(Workorder, pk=id)
        form = WorkorderNoteForm(request.POST, instance=item)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderInfoChanged'})
    form = WorkorderNoteForm(instance=item)
    context = {
        #'notes':notes,
        'form':form,
        'pk': pk,
    }
    return render(request, 'workorders/modals/notes.html', context) 

@login_required
def readnotes(request, pk=None):
    item = get_object_or_404(WorkorderItem, pk=pk)
    if request.method == "POST":
    #     id = request.POST.get('id')
    #     print(id)
    #     item = get_object_or_404(WorkorderItem, pk=id)
    #     form = NoteForm(request.POST, instance=item)
    #     if form.is_valid():
    #             form.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = NoteForm(instance=item)
    context = {
        #'notes':notes,
        'form':form,
        'pk': pk,
    }
    return render(request, 'workorders/modals/notes.html', context) 
            


@login_required
def quote_to_workorder(request):
    quote = request.GET.get('quote')
    n = Numbering.objects.get(name='Workorder Number')
    workorder_number = n.value
    try:
        item = Workorder.objects.get(workorder = quote)
        if item.quote == 0:
            return redirect("workorders:overview", id=item.workorder)
        print(item.workorder)
        print(item.quote)
        print('total')
        print(item.workorder_total)
        item.quoted_price = item.workorder_total
        item.workorder = workorder_number
        item.quote = 0
        item.save()
    except Exception as e:
        raise e
    print(quote)
    try:
        items = WorkorderItem.objects.filter(workorder_hr = quote)
        for item in items:
            item.workorder_hr = workorder_number
            item.save()
    except Exception as e:
        raise e
    try:
        items = KruegerJobDetail.objects.filter(hr_workorder = quote)
        for item in items:
            item.hr_workorder = workorder_number
            item.save()
    except Exception as e:
        raise e
    try:
        items = WideFormat.objects.filter(hr_workorder = quote)
        for item in items:
            item.hr_workorder = workorder_number
            item.save()
    except Exception as e:
        raise e
    try:
        items = OrderOut.objects.filter(hr_workorder = quote)
        for item in items:
            item.hr_workorder = workorder_number
            item.save()
    except Exception as e:
        raise e
    try:
        items = SetPrice.objects.filter(hr_workorder = quote)
        for item in items:
            item.hr_workorder = workorder_number
            item.save()
    except Exception as e:
        raise e
    try:
        items = Photography.objects.filter(hr_workorder = quote)
        for item in items:
            item.hr_workorder = workorder_number
            item.save()
    except Exception as e:
        raise e
    print(n.value)
    inc = int('1')
    n.value = n.value + inc
    print(n.value)
    n.save()
    return redirect("workorders:overview", id=workorder_number)

@login_required
def abandon_quote(request):
    quote = request.GET.get('quote')
    print(quote)
    try:
        Workorder.objects.filter(workorder = quote).update(abandon_quote=1)
    except:
        pass
    return redirect("dashboard:dashboard")



@login_required
def complete_status(request):
    workorder = request.GET.get('workorder')
    print(workorder)
    parent = WorkorderItem.objects.filter(workorder=workorder, parent=1)
    parent.update(absolute_price = 0, tax_amount = 0, total_with_tax = 0)
    for p in parent:
        #absolute price
        ap = 0
        #tax amount
        ta = 0
        #total with tax
        twt = 0
        childs = WorkorderItem.objects.filter(parent_item=p.id)
        for c in childs:
            x = WorkorderItem.objects.get(pk=c.id)
            if x.billable:
                try:
                    ap = ap + x.absolute_price
                except:
                    pass
                try:
                    ta = ta + x.tax_amount
                except:
                    pass
                try:
                    twt = twt + x.total_with_tax
                except:
                    pass
                print(twt)
        print(twt)
        parent = WorkorderItem.objects.get(pk=p.id)
        parent.absolute_price = ap
        parent.tax_amount = ta
        parent.total_with_tax = twt
        parent.save()
    item = Workorder.objects.get(id = workorder)
    total_invoice = WorkorderItem.objects.filter(workorder_id=workorder).exclude(billable=0).exclude(parent=1).aggregate(
            sum=Sum('total_with_tax'),
            tax=Sum('tax_amount'),
            abs=Sum('absolute_price')
            )
    #total_invoice = list(WorkorderItem.objects.aggregate(Sum('total_with_tax')).values())[0]
    #total_with_tax = list(total_invoice.values())[0]
    tax = list(total_invoice.values())[1]
    subtotal = list(total_invoice.values())[2]
    if not subtotal:
        subtotal = 0
    subtotal = round(subtotal, 2)
    tax = round(tax, 2)
    if not tax:
        tax = 0
    tax_percent = Decimal.from_float(.055)
    tax_amount = Decimal.from_float(1.055)
    abs_tax = subtotal * tax_percent
    abs_tax = round(abs_tax, 2)
    total = subtotal + tax

    if item.completed == 0:
        item.total_balance = total
        item.open_balance = total
        item.updated = timezone.now()
        item.date_completed = timezone.now()
        item.workorder_total = total
        item.subtotal = subtotal
        item.tax = tax
        if not item.amount_paid:
            item.amount_paid = 0
        item.completed = 1
        #item.total_balance = 
        item.save()
    else:
        if not item.amount_paid:
            item.amount_paid = 0
        item.completed = 0
        item.total_balance = 0
        item.open_balance = 0
        item.checked_and_verified = 0
        item.updated = timezone.now()
        item.date_completed = None
        item.workorder_total = 0
        item.subtotal = 0
        item.tax = 0
        item.save()
    cust = item.customer_id
    #open_balance = Workorder.objects.filter(customer_id=cust).exclude(billed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
    open_balance = Workorder.objects.filter(customer_id=cust).exclude(completed=0).exclude(paid_in_full=1).exclude(quote = 1).aggregate(Sum('open_balance'))
    open_balance = list(open_balance.values())[0]
    print('open balance')
    print(open_balance)
    if open_balance:
        open_balance = round(open_balance, 2)
    else:
        open_balance = total
    #print(open_balance)
    new_high = Customer.objects.get(id=cust)
    if new_high.high_balance:
        if open_balance > new_high.high_balance:
            high_balance = open_balance
        else:
            high_balance = new_high.high_balance
    else: 
        print(total)
        high_balance = total
    Customer.objects.filter(pk=cust).update(open_balance = open_balance, high_balance = high_balance)
    return redirect("workorders:overview", id=item.workorder)

@login_required
def billable_status(request, id):
    item = id
    item = WorkorderItem.objects.get(id=item)
    if item.billable == 0:
        item.billable = 1
        item.save()
        billable = True
    else:
        item.billable = 0
        item.save()
        billable = False
    context = {
        'id':id,
        'billable':billable,
    }
    return render(request, 'workorders/partials/billable.html', context)

@login_required
def item_status(request, pk=None):
    item = get_object_or_404(WorkorderItem, pk=pk)
    if request.method == "POST":
        id = request.POST.get('id')
        print(id)
        item = get_object_or_404(WorkorderItem, pk=id)
        form = JobStatusForm(request.POST, instance=item)
        if form.is_valid():
                obj = form.save(commit=False)
                completed = obj.completed
                if obj.job_status == '6':
                    obj.completed = 1
                else:
                    obj.completed = 0
                if completed == 1:
                    obj.job_status_id = 6
                    obj.completed = 1
                obj.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = JobStatusForm(instance=item)
    context = {
        #'notes':notes,
        'form':form,
        'pk': pk,
    }
    return render(request, 'workorders/modals/item_status.html', context) 

@login_required
def stale(request, pk=None):
    item = get_object_or_404(WorkorderItem, pk=pk)
    if item:
        WorkorderItem.objects.filter(pk=pk).update(updated = timezone.now())
        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'}) 
    
def billed(request, id):
    workorder = get_object_or_404(Workorder, pk=id)
    print(workorder.workorder)
    workorder.date_billed = timezone.now()
    workorder.billed = 1
    workorder.save()
    return redirect('workorders:overview', id=workorder.workorder)

@login_required
def task_notes(request, pk=None, task=None):
    item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
    #item = KruegerJobDetail.objects.get(workorder_item = id)
    print(task)
    if request.method == "POST":
        id = request.POST.get('id')
        print(id)
        note = request.POST.get('notes')
        if not note:
            print('empty')
            note = None
        print(note)
        print('note')
        print(note)
        #item = get_object_or_404(WorkorderItem, pk=id)
        item = get_object_or_404(KruegerJobDetail, workorder_item = id)
        if task == 'mailmerge_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(mailmerge_note = note)
        if task == 'pad_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(pad_note = note)
        if task == 'perf_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(perf_note = note)
        if task == 'numbering_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(numbering_note = note)
        if task == 'wraparound_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(wraparound_note = note)
        if task == 'drill_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(drill_note = note)
        if task == 'staple_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(staple_note = note)
        if task == 'fold_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(fold_note = note)
        if task == 'tab_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(tab_note = note)
        if task == 'bulkmail_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(bulkmail_note = note)
        if task == 'misc1_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(misc1_note = note)
        if task == 'misc2_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(misc2_note = note)
        if task == 'misc3_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(misc3_note = note)
        if task == 'misc4_note':
            KruegerJobDetail.objects.filter(workorder_item = id).update(misc4_note = note)

        return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    #form = TaskNoteForm(instance=item)
    print(item.perf_note)
    context = {
        #'notes':notes,
        #'form':form,
        'item': item,
        'task': task,
        'pk': pk,
    }
    return render(request, 'workorders/modals/task_notes.html', context) 

@login_required
def void_workorder(request, pk=None, void=None):
    if request.method == "POST":
        memo = request.POST.get('memo')
        if not void:
            void = request.POST.get('void') 
            #if void is False:
            #    void = 0
        if pk is None: 
            pk = request.POST.get('pk')
        print('void')
        print(void)
        print('pk')
        print(pk)       
        #workorder = Workorder.objects.get(pk=pk)
        if void == '0':
            if not memo:
                message = 'Memo is required'
                context = {
                    'message':message,
                    'pk':pk,
                }
                return render (request, "workorders/modals/void_workorder_modal.html", context)
                print('no memo')
            Workorder.objects.filter(pk=pk).update(void = 1, billed = 0, void_memo=memo)
            items = WorkorderItem.objects.filter(workorder_id=pk)
            for x in items:
                print(x.pk)
                WorkorderItem.objects.filter(pk=x.pk).update(void=1, void_memo=memo)
            print(1)
        if void == 1:
            Workorder.objects.filter(pk=pk).update(void = 0, void_memo=memo)
            print(2)
        return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderVoid'})
    #print('hello')
    pk = request.GET.get('pk')
    #print(pk)
    context = {
        'pk':pk,
    }
    return render (request, "workorders/modals/void_workorder_modal.html", context)

@login_required
def void_status(request):
    pk = request.GET.get('workorder')
    print('workorder')
    print(pk)
    workorder = Workorder.objects.get(pk=pk)
    void = workorder.void
    paid = workorder.paid_in_full
    billed = workorder.billed
    customer = workorder.customer.id
    print(customer)
    print('void')
    print(void)
    context = {
        'void':void,
        'paid':paid,
        'billed':billed,
        'customer':customer,
    }
    return render(request, 'workorders/partials/void_status.html', context)

def close_pay_modal(request):
    print('test')
    return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderVoid'})

def complete_allitems(request):
    workorders = Workorder.objects.filter().exclude(completed=0)
    for x in workorders:
        print(x.workorder)
        item = WorkorderItem.objects.filter(workorder_hr=x.workorder)
        for y in item:
            print(y.workorder_hr)
            WorkorderItem.objects.filter(pk=y.pk).update(job_status_id=6, completed=1)
    return redirect('dashboard:dashboard')
    
@login_required
def item_details(request, pk=None):
    item = get_object_or_404(WorkorderItem, pk=pk)
    if request.method == "POST":
        id = request.POST.get('id')
        print(id)
        item = get_object_or_404(WorkorderItem, pk=id)
        form = ItemDetailForm(request.POST, instance=item)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    form = ItemDetailForm(instance=item)
    context = {
        #'notes':notes,
        'form':form,
        'pk': pk,
    }
    return render(request, 'workorders/modals/item_details.html', context) 

@login_required
def verify(request, pk=None):
    workorder = Workorder.objects.get(pk=pk)
    item = Workorder.objects.filter(pk=pk).update(checked_and_verified=1)
    print(workorder.workorder)
    return redirect('workorders:overview', id=workorder.workorder)

@login_required
def invoice_sent(request, pk=None):
    workorder = Workorder.objects.get(pk=pk)
    item = Workorder.objects.filter(pk=pk).update(invoice_sent=1)
    print(workorder.workorder)
    return redirect('workorders:overview', id=workorder.workorder)


@login_required
def orderout_wait(request):
    workorder = request.GET.get('workorder')
    print(workorder)
    
    item = Workorder.objects.get(id = workorder)
    
    if item.orderout_waiting == 0:
        item.orderout_waiting = 1
        item.updated = timezone.now()
        #item.total_balance = 
        item.save()
    else:
        item.orderout_waiting = 0
        item.updated = timezone.now()
        item.save()
    return redirect("workorders:overview", id=item.workorder)
