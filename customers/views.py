from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse
from customers.models import Customer, Contact
from customers.forms import CustomerForm, ContactForm
from controls.models import Numbering
from workorders.models import Workorder
from workorders.forms import WorkorderForm


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
    return render(request, "customers/partials/customer_info.html", {
        #'customer': customer,
        'customer': customer,
        'contact': contact,
        'form': WorkorderForm(),
    })

def contacts(request):
    customer = request.GET.get('customer')
    print('customer')
    print(customer)
    contact = Contact.objects.filter(customer=customer)
    context = {
        'customer': customer,
        'contacts': contact
        }
    #print(contacts)
    return render(request, 'customers/partials/contacts.html', context)

def customers(request):
    customer = Customer.objects.all()
    context = {
        'customers': customer
        }
    #print(customer)
    #print(contacts)
    return render(request, 'customers/partials/customers.html', context)

def customer_list(request):
    customer = Customer.objects.all()
    context = {
        'customers': customer
        }
    return render(request, 'customers/list.html', context)


def new_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            ##Increase workorder numbering
            n = Numbering.objects.get(pk=2)
            form.instance.customer_number = n.value
            #workorder = n.value
            inc = int('1')
            n.value = n.value + inc
            print(n.value)
            #n.save() -- Save in the if statement below
            ## End of numbering
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
                return render(request, 'customers/modals/newcustomer_form.html', context)
            if not cn:
                print('Empty string')
                print(fn)
                print(ln)
                form.instance.company_name = fn + ' ' + ln
                #print(obj.company_name)
                form.save()
                n.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
            if cn:
                print(cn)
                form.save()
                n.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
            #obj.save
            #form.save()
            #return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
    else:
        form = CustomerForm()
    return render(request, 'customers/modals/newcustomer_form.html', {
        'form': form,
    })

def new_contact(request):
    customer = request.GET.get('customer')
    workorder = request.GET.get('workorder')
    print(customer)
    print(workorder)
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            company_num = request.POST.get("customer")
            workorder = request.POST.get("workorder")
            print(workorder)
            form.instance.customer_id = company_num
            print(company_num)
            print(form.instance.id)
            form.save()
            if workorder:
                contact = form.instance.id
                Workorder.objects.filter(pk=workorder).update(contact_id=contact)
                #obj = get_object_or_404(Workorder, pk=workorder)
                #form2 = 
                print(form.instance.id)
                print('else')
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
    else:
        form = ContactForm()
        context = {
            'form': form,
            'customer': customer,
            'workorder': workorder
        }
    return render(request, 'customers/modals/newcontact_form.html', context)

def new_cust_contact(request):
    customer = request.GET.get('customer')
    #workorder = request.GET.get('workorder')
    print('hello')
    print('test')
    print(customer)
    #print(workorder)
    if request.method == "POST":
        print('test')
        form = ContactForm(request.POST)
        if form.is_valid():
            company_num = request.POST.get("customer")
            #workorder = request.POST.get("workorder")
            #print(workorder)
            form.instance.customer_id = company_num
            print('companynum')
            print(company_num)
            print(form.instance.id)
            form.save()
            # if workorder:
            #     contact = form.instance.id
            #     Workorder.objects.filter(pk=workorder).update(contact_id=contact)
            #     #obj = get_object_or_404(Workorder, pk=workorder)
            #     #form2 = 
            #     print(form.instance.id)
            #     print('else')
            #return render(request, 'customers/partials/customer_info.html')
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactAdded'})
    else:
        form = ContactForm()
        context = {
            'form': form,
            'customer': customer,
            #'workorder': workorder
        }
    return render(request, 'customers/modals/newcontact_form.html', context)

def edit_customer(request):
    customer = request.GET.get('customer')
    if request.method == "POST":
        company_num = request.POST.get("customer")
        print(company_num)
        obj = get_object_or_404(Customer, pk=company_num)
        print('hello')
        form = CustomerForm(request.POST, instance=obj)
        if form.is_valid():
            c = request.POST.get('customer')
            cn = request.POST.get('company_name')
            fn = request.POST.get('first_name')
            ln = request.POST.get('last_name')
            if not cn and not fn and not ln:
                message = 'Please fill in Company name or Customer Name'
                context = {
                    'message': message,
                    'form': form,
                    'customer': c
                }
                return render(request, 'customers/modals/edit_customer.html', context)
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
            #form.save()
            #return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerEdit'})
    else:
        obj = get_object_or_404(Customer, id=customer)
        form = CustomerForm(instance=obj)
        context = {
            'form': form,
            'customer': customer
        }
    return render(request, 'customers/modals/edit_customer.html', context)

def cust_info(request):
    if request.htmx:
        customer = request.GET.get('customer')
        print(customer)
        customer = Customer.objects.get(id=customer)
        print(customer.id)
        context = { 'customer': customer,}
        return render(request, 'customers/partials/customer_info.html', context)
    #print('hello')
    # workorder = Workorder.objects.get(workorder=id)
    # customer = Customer.objects.get(id=workorder.customer_id)
    # if workorder.contact_id:
    #     contact = Contact.objects.get(id=workorder.contact_id)
    # else: 
    #     contact = ''
    # context = {
    #         'workorder': workorder,
    #         'customer': customer,
    #         'contact': contact,
    #     }
    #return render(request, 'customers/partials/customer_info.html', context)

def contact_info(request):
    if request.htmx:
        changeworkorder = request.GET.get('workorder')
        changecustomer = request.GET.get('customer')
        workorder = Workorder.objects.get(id=changeworkorder)
        contact = workorder.contact_id
        print(contact)
        if contact:
            print(contact)
            print('test')
            contact = Contact.objects.get(id=contact)
            print(contact.id)
            context = { 'contact': contact,
                        'changecustomer':changecustomer,
                        'changeworkorder':changeworkorder
                       }
            return render(request, 'customers/partials/contact_info.html', context)
        workorder = request.GET.get('workorder')
        print(workorder)
        contact = Workorder.objects.get(id=workorder)
        print(contact.contact_id)
        contact = contact.contact_id
        print(contact)
        contact = Contact.objects.get(id=contact)
        context = { 'contact': contact,}
        return render(request, 'customers/partials/contact_info.html', context)
    workorder = Workorder.objects.get(workorder=id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    context = {
            'workorder': workorder,
            'contact': contact,
            'changecustomer':changecustomer,
            'changeworkorder':changeworkorder
        }
    return render(request, 'customers/partials/contact_info.html', context)

def edit_contact(request):
    contact = request.GET.get('contact')
    #customer = request.GET.get('customer')
    if request.method == "POST":
        contact_num = request.POST.get("contact")
        obj = get_object_or_404(Contact, pk=contact_num)
        #obj = (Contact, pk=contact_num)
        form = ContactForm(request.POST, instance=obj)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
    else:
        if not contact:
            workorder = request.GET.get('workorder')
            contact = Workorder.objects.get(id=workorder)
            contact = contact.contact_id
        obj = get_object_or_404(Contact, id=contact)
        form = ContactForm(instance=obj)
        context = {
            'form': form,
            'contact': contact
        }
    return render(request, 'customers/modals/edit_contact.html', context)

def change_contact(request):
    customer = request.GET.get('customer')
    workorder = request.GET.get('workorder')
    if request.method == "POST":
        contact = request.POST.get('contacts')
        workorder = request.POST.get('workorder')
        #obj = get_object_or_404(Workorder, pk=workorder)
        #form = WorkorderForm
        print(contact)
        print(workorder)
        obj = Workorder.objects.get(id=workorder)
        obj.contact_id = contact
        obj.save(update_fields=['contact_id'])
        print('here')
        return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
    print(customer)
    print(workorder)
    obj = Contact.objects.filter(customer=customer)
    context = {
        'obj': obj,
        'workorder': workorder
    }
    return render(request, 'customers/modals/change_contact.html', context)