from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse
from customers.models import Customer, Contact
from customers.forms import CustomerForm, ContactForm
from .models import Workorder, Numbering
from .forms import WorkorderForm

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
    context = {
        'customers': customer,
        #'newcustomerform': newcustomerform,
        'form': WorkorderForm(),
        #'workordernum': workordernum,
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
            return redirect("workorders:items", id=workorder)
            #return render(request, "workorders/items.html", context)
    return render(request, "workorders/create.html", context)


def test_base(request):
    return render(request, "workorders/testcreate.html", {
        'customers': Customer.objects.all(),
        'form': WorkorderForm(),
    })

def customer_info(request):
    if request.htmx:
        customer = request.GET.get('customer')
        contact = request.GET.get('contacts')
        if contact:
            contact = Contact.objects.get(id=contact)
        if customer:
            customer = Customer.objects.get(id=customer)
        print(contact)
        #print(customer)
    #print(customer.company_name)
    #customer = request.POST.get('customers.id')
    #customer = get_object_or_404(Customer, id=company)
    return render(request, "workorders/partials/customer_info.html", {
        #'customer': customer,
        'customer': customer,
        'contact': contact,
        'form': WorkorderForm(),
    })

def contacts(request):
    customer = request.GET.get('customer')
    #print(customer)
    contact = Contact.objects.filter(customer=customer)
    context = {
        'customer': customer,
        'contacts': contact
        }
    #print(contacts)
    return render(request, 'workorders/partials/contacts.html', context)

def customers(request):
    customer = Customer.objects.all()
    context = {
        'customers': customer
        }
    #print(customer)
    #print(contacts)
    return render(request, 'workorders/partials/customers.html', context)

def new_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            #obj = form.save(commit=False)
            #customer = request.POST.get("company_name")
            #print(customer)
            cn = request.POST.get('company_name')
            fn = request.POST.get('first_name')
            ln = request.POST.get('last_name')
            if not cn and not fn and not ln:
                message = 'Please fill in Company name or Customer Name'
                context = {
                    'message': message,
                    'form': form
                }
                return render(request, 'workorders/modals/newcustomer_form.html', context)
            if not cn:
                print('Empty string')
                print(fn)
                print(ln)
                form.instance.company_name = fn + ' ' + ln
                #print(obj.company_name)
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
            if cn:
                print(cn)
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
            #obj.save
            #form.save()
            #return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
    else:
        form = CustomerForm()
    return render(request, 'workorders/modals/newcustomer_form.html', {
        'form': form,
    })

def new_contact(request):
    customer = request.GET.get('customer')
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            company_num = request.POST.get("customer")
            form.instance.customer_id = company_num
            print(company_num)
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactAdded'})

    else:
        form = ContactForm()
        context = {
            'form': form,
            'customer': customer
        }
    return render(request, 'workorders/modals/newcontact_form.html', context)

def items(request, id):
    workorder = Workorder.objects.get(workorder=id)
    customer = Customer.objects.get(id=workorder.customer_id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
        # context = {
        #     'workorder': workorder,
        #     'customer': customer,
        #     'contact': contact,
        # }
        # return render(request, "workorders/items.html", context)
    else: 
        contact = ''
    context = {
            'workorder': workorder,
            'customer': customer,
            'contact': contact,
        }
    return render(request, "workorders/items.html", context)

def workorder_list(request):
    workorder = Workorder.objects.all()
    context = {
        'workorders': workorder,
    }
    return render(request, 'workorders/list.html', context)

def edit_customer(request):
    customer = request.GET.get('customer')
    #print(customer)
    #customer = 12
    #obj = get_object_or_404(Customer, id=customer)
    #form = CustomerForm(instance=obj)
    print(customer)
    print('hi')
    if request.method == "POST":
        company_num = request.POST.get("customer")
        print(company_num)
        obj = get_object_or_404(Customer, pk=company_num)
        print('hello')
        form = CustomerForm(request.POST, instance=obj)
        #print(form.errors)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerEdit'})
    else:
        obj = get_object_or_404(Customer, id=customer)
        form = CustomerForm(instance=obj)
        context = {
            'form': form,
            'customer': customer
        }
    return render(request, 'workorders/modals/edit_customer.html', context)



def new_contact(request):
    customer = request.GET.get('customer')
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            company_num = request.POST.get("customer")
            form.instance.customer_id = company_num
            print(company_num)
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactAdded'})

    else:
        form = ContactForm()
        context = {
            'form': form,
            'customer': customer
        }
    return render(request, 'workorders/modals/newcontact_form.html', context)

def cust_info(request):
    workorder = Workorder.objects.get(workorder=id)
    customer = Customer.objects.get(id=workorder.customer_id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    context = {
            'workorder': workorder,
            'customer': customer,
            'contact': contact,
        }
    return render(request, 'workorders/partials/cust_info.html', context)