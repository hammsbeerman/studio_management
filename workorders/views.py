from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from customers.models import Customer, Contact
from .models import Workorder, Numbering, Category, DesignType, WorkorderItem, SubCategory
from .forms import WorkorderForm, WorkorderNewItemForm, WorkorderItemForm
from krueger.forms import KruegerJobDetailForm
from krueger.models import KruegerJobDetail

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
    categories = Category.objects.all().distinct()
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
        if form.is_valid():
            form.instance.customer_id = request.POST.get('customer')
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
            n = Numbering.objects.get(pk=1)
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

def overview(request, id=None):
    workorder = Workorder.objects.get(workorder=id)
    #if not workorder:
    #    workorder = request.GET.get('workorder')
    customer = Customer.objects.get(id=workorder.customer_id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    history = Workorder.objects.filter(customer_id=customer).order_by("-workorder")[:10]
    workid = workorder.id
    categories = Category.objects.all().distinct()
    context = {
            'workid': workid,
            'workorder': workorder,
            'customer': customer,
            'contact': contact,
            'history': history,
            'categories':categories,
        }
    return render(request, "workorders/overview.html", context)

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

def workorder_list(request):
    workorder = Workorder.objects.all().exclude(workorder=1111)
    context = {
        'workorders': workorder,
    }
    return render(request, 'workorders/list.html', context)

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
                return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderUpdated'})
    else:
        obj = get_object_or_404(Workorder, id=workorder)
        form = WorkorderForm(instance=obj)
        context = {
            'form': form,
            'workorder': workorder
        }
    return render(request, 'workorders/modals/edit_workorder.html', context)

def workorder_info(request):
    if request.htmx:
        workorder = request.GET.get('workorder')
        print(workorder)
        workorder = Workorder.objects.get(pk=workorder)
        context = { 'workorder': workorder,}
        return render(request, 'workorders/partials/workorder_info.html', context)
    
##########Add Items
def add_item(request, parent_id):
    print(parent_id)
    categories = Category.objects.all()
    if request.method == "POST":
        form = WorkorderNewItemForm(request.POST)
        desc = request.POST.get('description')
        cat = request.POST.get('category')
        subcat = request.POST.get('subcategory')
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
            #obj = request.POST.get
            parent = Workorder.objects.get(pk=parent_id)
            #Add workorder to form since it wasn't displayed
            obj.workorder_id = parent_id
            print('parent')
            print(parent.workorder)
            obj.workorder_hr = parent.workorder
            #obj.item_subcategory = subcategory
            obj.save()
            print(obj.pk)
            print(parent.customer)
            print(parent.customer_id)
            #print(parent.category)
            detailbase = KruegerJobDetail(workorder = parent.id, hr_workorder=parent.workorder, workorder_item =obj.pk, internal_company = parent.internal_company,
                                          customer_id=parent.customer_id, hr_customer=parent.hr_customer, category = cat, subcategory = subcat, description = desc)
            detailbase.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    else:
        form = WorkorderNewItemForm()
        categories = Category.objects.all().distinct()
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'workorders/modals/new_item_form.html', context)

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
        obj = WorkorderItem.objects.filter(workorder_id=id)
        #print(obj.id)
        #print(obj)
    except:
        obj = None
    if obj is  None:
        return HttpResponse("Not found.")
    context = {
        "items": obj
    }
    return render(request, "workorders/partials/item_list.html", context) 



def edit_print_item(request):
    pass






def edit_design_item(request, pk, cat):
    item = get_object_or_404(WorkorderItem, pk=pk)
    category = cat
    if request.method == "POST":
        print('hello')
        category = request.POST.get('cat')
        form = WorkorderItemForm(request.POST, instance=item)
        #form.instance.item_category = category
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
        else:
            print(form.errors)
    print(category)
    obj = Category.objects.get(id=category)        
    print(obj.name)
    form = WorkorderItemForm(instance=item)
    context = {
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
    }
    return render(request, 'workorders/modals/design_item_form.html', context)


@ require_POST
def remove_workorder_item(request, pk):
    item = get_object_or_404(WorkorderItem, pk=pk)
    item.delete()
    return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})


def copy_workorder_item(request, pk, workorder=None):
    #Copy line item to current workorder
    if workorder:
        obj = WorkorderItem.objects.get(pk=pk)
        obj.pk = None
        obj.save()
        #print(obj.pk)
        #print(pk)
        #Copy coresponding kruegerjobdetail item
        objdetail = KruegerJobDetail.objects.get(workorder_item=pk)
        objdetail.pk = None
        objdetail.workorder_item = obj.pk
        objdetail.last_item_order = obj.workorder_hr
        objdetail.last_item_price = objdetail.price_total
        objdetail.save()
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
        objdetail = KruegerJobDetail.objects.get(workorder_item=pk)
        objdetail.pk = None
        objdetail.workorder_item = obj.pk
        objdetail.workorder = new.pk
        objdetail.hr_workorder = new.workorder
        objdetail.last_item_order = last_workorder
        objdetail.last_item_price = objdetail.price_total
        objdetail.save()
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
def copy_workorder(request, id=None):
    print (id)
    #Get data from current workorder
    obj = Workorder.objects.get(id=id)
    lastworkorder = obj.workorder
    n = Numbering.objects.get(pk=1)
    obj.workorder = n.value
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
        objdetail = KruegerJobDetail.objects.get(workorder_item=oldid)
        objdetail.pk = None
        objdetail.workorder_item = item.pk
        objdetail.workorder = new_workorder_id
        objdetail.hr_workorder = newworkorder
        objdetail.last_item_order = lastworkorder
        objdetail.last_item_price = objdetail.price_total
        objdetail.save()
    return redirect('workorders:overview', id=newworkorder)

def subcategory(request):
    cat = request.GET.get('item_category')
    print(cat)
    obj = SubCategory.objects.filter(category_id=cat)
    context = {
        'obj':obj
    }
    return render(request, 'workorders/modals/subcategory.html', context) 












            # form.instance.workorder = n.value
            # workorder = n.value
            # inc = int('1')
            # n.value = n.value + inc
            # print(n.value)
            # n.save()
            # ## End of numbering
            # print('hello')
            # form.save()
            # context = {
            #     'id': n.value,
            # }
            # return redirect("workorders:overview", id=workorder)












    # if request.method == "GET":
    #     obj = WorkorderItem.objects.get(pk=pk)
    #     obj.pk = None
    #     obj.save()
    #     # message = 'Item duplicated'
    #     # context ={
    #     #     'message': message
    #     # }
    #     return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    # if request.method == "POST":
    #     workorder = request.POST.get('workorder')
    #     parent = Workorder.objects.get(workorder=workorder)
    #     print(parent.pk)
    #     obj = WorkorderItem.objects.get(pk=pk)
    #     obj.pk = None
    #     obj.workorder_hr = workorder
    #     obj.workorder_id = parent.pk
    #     obj.save()
    #     return HttpResponse(status=204, headers={'HX-Trigger': 'Item Added'})
    # obj = WorkorderItem.objects.get(pk=pk)
    # context = {
    #     'obj': obj,
    #     #'workorder': workorder
    # }
    # return render(request, 'workorders/modals/copy_item.html', context)













###########
    


    



# def customer_info(request):
#     if request.htmx:
#         customer = request.GET.get('customer')
#         contact = request.GET.get('contacts')
#         if contact:
#             contact = Contact.objects.get(id=contact)
#         if customer:
#             customer = Customer.objects.get(id=customer)
#         print(contact)
#         #print(customer)
#     #print(customer.company_name)
#     #customer = request.POST.get('customers.id')
#     #customer = get_object_or_404(Customer, id=company)
#     return render(request, "customers/partials/customer_info.html", {
#         #'customer': customer,
#         'customer': customer,
#         'contact': contact,
#         'form': WorkorderForm(),
#     })

# def contacts(request):
#     customer = request.GET.get('customer')
#     #print(customer)
#     contact = Contact.objects.filter(customer=customer)
#     context = {
#         'customer': customer,
#         'contacts': contact
#         }
#     #print(contacts)
#     return render(request, 'customers/partials/contacts.html', context)

# def customers(request):
#     customer = Customer.objects.all()
#     context = {
#         'customers': customer
#         }
#     #print(customer)
#     #print(contacts)
#     return render(request, 'customers/partials/customers.html', context)

# def new_customer(request):
#     if request.method == "POST":
#         form = CustomerForm(request.POST)
#         if form.is_valid():
#             #obj = form.save(commit=False)
#             #customer = request.POST.get("company_name")
#             #print(customer)
#             cn = request.POST.get('company_name')
#             fn = request.POST.get('first_name')
#             ln = request.POST.get('last_name')
#             if not cn and not fn and not ln:
#                 message = 'Please fill in Company name or Customer Name'
#                 context = {
#                     'message': message,
#                     'form': form
#                 }
#                 return render(request, 'customers/modals/newcustomer_form.html', context)
#             if not cn:
#                 print('Empty string')
#                 print(fn)
#                 print(ln)
#                 form.instance.company_name = fn + ' ' + ln
#                 #print(obj.company_name)
#                 form.save()
#                 return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
#             if cn:
#                 print(cn)
#                 form.save()
#                 return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
#             #obj.save
#             #form.save()
#             #return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
#     else:
#         form = CustomerForm()
#     return render(request, 'customers/modals/newcustomer_form.html', {
#         'form': form,
#     })

# def new_contact(request):
#     customer = request.GET.get('customer')
#     if request.method == "POST":
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             company_num = request.POST.get("customer")
#             form.instance.customer_id = company_num
#             print(company_num)
#             form.save()
#             return HttpResponse(status=204, headers={'HX-Trigger': 'ContactAdded'})

#     else:
#         form = ContactForm()
#         context = {
#             'form': form,
#             'customer': customer
#         }
#     return render(request, 'customers/modals/newcontact_form.html', context)

# def edit_customer(request):
#     customer = request.GET.get('customer')
#     #print(customer)
#     #customer = 12
#     #obj = get_object_or_404(Customer, id=customer)
#     #form = CustomerForm(instance=obj)
#     print(customer)
#     print('hi')
#     if request.method == "POST":
#         company_num = request.POST.get("customer")
#         print(company_num)
#         obj = get_object_or_404(Customer, pk=company_num)
#         print('hello')
#         form = CustomerForm(request.POST, instance=obj)
#         #print(form.errors)
#         if form.is_valid():
#             form.save()
#             return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerEdit'})
#     else:
#         obj = get_object_or_404(Customer, id=customer)
#         form = CustomerForm(instance=obj)
#         context = {
#             'form': form,
#             'customer': customer
#         }
#     return render(request, 'customers/modals/edit_customer.html', context)



# def new_contact(request):
#     customer = request.GET.get('customer')
#     if request.method == "POST":
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             company_num = request.POST.get("customer")
#             form.instance.customer_id = company_num
#             print(company_num)
#             form.save()
#             return HttpResponse(status=204, headers={'HX-Trigger': 'ContactAdded'})

#     else:
#         form = ContactForm()
#         context = {
#             'form': form,
#             'customer': customer
#         }
#     return render(request, 'customers/modals/newcontact_form.html', context)

# def cust_info(request):
#     if request.htmx:
#         customer = request.GET.get('customer')
#         print(customer)
#         customer = Customer.objects.get(id=customer)
#         print(customer.id)
#         context = { 'customer': customer,}
#         return render(request, 'customers/partials/customer_info.html', context)
#     workorder = Workorder.objects.get(workorder=id)
#     customer = Customer.objects.get(id=workorder.customer_id)
#     if workorder.contact_id:
#         contact = Contact.objects.get(id=workorder.contact_id)
#     else: 
#         contact = ''
#     context = {
#             'workorder': workorder,
#             'customer': customer,
#             'contact': contact,
#         }
#     return render(request, 'customers/partials/customer_info.html', context)