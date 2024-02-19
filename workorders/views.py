from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count, Min, Sum
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from customers.models import Customer, Contact
from controls.models import Numbering, Category, SubCategory, SetPriceItem, SetPriceItemPrice
from .models import Workorder, DesignType, WorkorderItem
from .forms import WorkorderForm, WorkorderNewItemForm, WorkorderItemForm, DesignItemForm, NoteForm, WorkorderNoteForm, CustomItemForm
from krueger.forms import KruegerJobDetailForm
from krueger.models import KruegerJobDetail
from inventory.forms import OrderOutForm, SetPriceForm, PhotographyForm
from inventory.models import OrderOut, SetPrice, Photography

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
    categories = Category.objects.all().distinct().order_by('name')
    context = {
        'customers': customer,
        #'newcustomerform': newcustomerform,
        'form': WorkorderForm(),
        #'workordernum': workordernum,
        'categories':categories,
    }
    if request.method == "POST":
        print('hi')
        form = WorkorderForm(request.POST)
        #print(form.internal_company)
        print(form.errors)
        quote = request.POST.get('quote')
        form.fields['quote'].choices = [(quote, quote)]
        if form.is_valid():
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
                n = Numbering.objects.get(name='Quote Number')
                form.instance.quote_number = n.value
                form.instance.workorder = n.value
                print(n.value)
            else: 
                print('workorder')
                n = Numbering.objects.get(name='Workorder Number')
                form.instance.workorder = n.value
            workorder = n.value
            inc = int('1')
            n.value = n.value + inc
            print(n.value)
            n.save()
            ## End of numbering
            print('hello')
            form.save()
            context = {
                'id': n.value,
            }
            return redirect("workorders:overview", id=workorder)
            #return render(request, "workorders/overview.html", context)
    return render(request, "workorders/create.html", context)

@login_required
def overview(request, id=None):
    workorder = Workorder.objects.get(workorder=id)
    #if not workorder:
    #    workorder = request.GET.get('workorder')
    customer = Customer.objects.get(id=workorder.customer_id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    print(id)
    history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).order_by("-workorder")[:5]
    workid = workorder.id
    categories = Category.objects.all().distinct().order_by('name')
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
def workorder_list(request):
    workorder = Workorder.objects.all().exclude(workorder=1111).exclude(quote=1)
    context = {
        'workorders': workorder,
    }
    return render(request, 'workorders/list.html', context)

@login_required
def quote_list(request):
    workorder = Workorder.objects.all().exclude(workorder=1111).exclude(quote=0)
    context = {
        'workorders': workorder,
    }
    return render(request, 'workorders/quotes.html', context)

@login_required
def edit_workorder(request):
    workorder = request.GET.get('workorder')
    #customer = request.GET.get('customer')
    if request.method == "POST":
        workorder_num = request.POST.get("workorder")
        obj = get_object_or_404(Workorder, pk=workorder_num)
        #obj = (Contact, pk=contact_num)
        form = WorkorderForm(request.POST, instance=obj)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderInfoChanged'})
    else:
        obj = get_object_or_404(Workorder, id=workorder)
        form = WorkorderForm(instance=obj)
        context = {
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
    categories = Category.objects.all().distinct().order_by('name')
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
            #obj.item_subcategory = subcategory
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
                if formname == DesignItemForm or formname == CustomItemForm:
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
        categories = Category.objects.all().distinct().order_by('name')
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
        print(id)
        completed = Workorder.objects.get(id=id)
        obj = WorkorderItem.objects.filter(workorder_id=id)
        subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).aggregate(Sum('absolute_price'))
        tax = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).aggregate(Sum('tax_amount'))
        total = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).aggregate(Sum('total_with_tax'))
        #override_total = WorkorderItem.objects.filter(workorder_id=id).exclude(override_price__isnull=True).aggregate(Sum('override_price'))
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
        "tax":tax,
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


@login_required
def edit_order_out_item(request, pk, cat):
    pass


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
            lineitem.tax_amount = lineitem.absolute_price * tax_percent
            lineitem.total_with_tax = lineitem.absolute_price * tax
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
            lineitem.tax_amount = lineitem.absolute_price * tax_percent
            lineitem.total_with_tax = lineitem.absolute_price * tax
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
            temp_total = override
        else:
            temp_total = total
        unit_price = temp_total / qty
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
            lineitem.tax_amount = lineitem.absolute_price * tax_percent
            lineitem.total_with_tax = lineitem.absolute_price * tax
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
        setprice = SetPriceItem.objects.get(id=item.setprice_category)
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
    setprice_category = SetPriceItem.objects.all()
    category = cat
    if request.method == "POST":
        form = SetPriceForm(request.POST, instance=item)
        obj = form.save(commit=False)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        #setpric = request.POST.get('unit_price')
        qty = obj.quantity
        total = obj.total_price
        override = obj.override_price
        #setprice_category = obj.setprice_item
        setprice_category = request.POST.get('setprice_category')
        setprice_item = request.POST.get('setprice_item')

       # print(setprice)
        #setprice_category = get_object_or_404(SetPriceItem, id=setprice)
        # setprice_item = SetPriceItem.objects.get(id=setprice)
        # print('name')
        # print(setprice_item.name)
        
        #print('setprice')
        #print(setprice_item.name)
        #print(setprice_item.description)
        if override:
            temp_total = override
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
            lineitem.tax_amount = lineitem.absolute_price * tax_percent
            lineitem.total_with_tax = lineitem.absolute_price * tax
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
        setpriceitem = SetPrice.objects.get(workorder_item=pk)
        setpriceitem.last_item_order = last_order
        setpriceitem.last_item_price = last_price
        setpriceitem.notes = notes
        setpriceitem.unit_price = unit_price
        setpriceitem.edited = 1
        setpriceitem.save()
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
    return render(request, 'workorders/modals/set_price_form.html', context)

        

















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


@ require_POST
@login_required
def remove_workorder_item(request, pk):
    item = get_object_or_404(WorkorderItem, pk=pk)
    item.delete()
    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})


@login_required
def copy_workorder_item(request, pk, workorder=None):
    #Copy line item to current workorder
    if workorder:
        print(pk)
        obj = WorkorderItem.objects.get(pk=pk)
        obj.pk = None
        obj.save()
        #print(obj.pk)
        #print(pk)
        #Copy coresponding kruegerjobdetail item
        try: 
            objdetail = KruegerJobDetail.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except:
            pass
        try:
            objdetail = OrderOut.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except:
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
        obj.last_item_price = obj.total_price
        # print(obj.last_item_order)
        obj.save()
        #Copy corresponding kruegerjobdetail to new object
        try:
            objdetail = KruegerJobDetail.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.workorder = new.pk
            objdetail.hr_workorder = new.workorder
            objdetail.last_item_order = last_workorder
            objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except:
            pass
        try:
            objdetail = OrderOut.objects.get(workorder_item=pk)
            objdetail.pk = None
            objdetail.workorder_item = obj.pk
            objdetail.last_item_order = obj.workorder_hr
            objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except:
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
    obj.workorder = n.value
    obj.quote_number = ''
    obj.completed = 0
    obj.original_order = lastworkorder
    #Increment workorder number
    newworkorder = obj.workorder
    #Update numbering table
    inc = int('1')
    n.value = n.value + inc
    n.save()
    #save workorder with new workorder number
    obj.pk=None
    obj.save()
    new_workorder_id=obj.pk
    print(id)
    print(newworkorder)
    #print(new_id)
    workorder_item = WorkorderItem.objects.filter(workorder_id=id)
    for item in workorder_item:
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
            objdetail.last_item_price = objdetail.price_total
            objdetail.save()
        except:
            pass
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
            lineitem.tax_amount = lineitem.absolute_price * tax_percent
            lineitem.total_with_tax = lineitem.absolute_price * tax_sum
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
        item.workorder = workorder_number
        item.quote = 0
        item.save()
    except:
        pass
    print(quote)
    try:
        items = WorkorderItem.objects.filter(workorder_hr = quote)
        for item in items:
            item.workorder_hr = workorder_number
            item.save()
    except:
        print('pass')
        pass
    try:
        items = OrderOut.objects.filter(workorder_hr = quote)
        for item in items:
            item.workorder_hr = workorder_number
            item.save()
    except:
        print('pass')
        pass
    try:
        items = SetPrice.objects.filter(workorder_hr = quote)
        for item in items:
            item.workorder_hr = workorder_number
            item.save()
    except:
        print('pass')
        pass
    try:
        items = Photography.objects.filter(workorder_hr = quote)
        for item in items:
            item.workorder_hr = workorder_number
            item.save()
    except:
        print('pass')
        pass
    print(n.value)
    inc = int('1')
    n.value = n.value + inc
    print(n.value)
    n.save()
    return redirect("workorders:overview", id=workorder_number)

@login_required
def complete_status(request):
    workorder = request.GET.get('workorder')
    print(workorder)
    item = Workorder.objects.get(id = workorder)
    if item.completed == 0:
        item.completed = 1
        item.save()
    else:
        item.completed = 0
        item.save()
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