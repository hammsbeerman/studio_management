from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Min, Sum
from django.utils import timezone
from django.http import HttpResponse
from .models import Customer, Contact
from .forms import CustomerForm, ContactForm, CustomerNoteForm
from controls.models import Numbering
from workorders.models import Workorder
from workorders.forms import WorkorderForm

@login_required
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

@login_required
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

@login_required
def customers(request):
    customer = Customer.objects.all().order_by('company_name')
    context = {
        'customers': customer
        }
    #print(customer)
    #print(contacts)
    return render(request, 'customers/partials/customers.html', context)

@login_required
def customer_list(request):
    customer = Customer.objects.all().order_by('company_name')
    context = {
        'customers': customer
        }
    return render(request, 'customers/list.html', context)


@login_required
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

@login_required
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
                try:
                    Workorder.objects.filter(pk=workorder).update(contact_id=contact)
                except:
                    return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
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

@login_required
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

@login_required
def edit_customer(request):
    customer = request.GET.get('customer')
    if request.method == "POST":
        company_num = request.POST.get("customer")
        print(company_num)
        obj = get_object_or_404(Customer, pk=company_num)
        print('hello')
        form = CustomerForm(request.POST, request.FILES, instance=obj)
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

@login_required
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

@login_required
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

@login_required
def details_contact_info(request):
    #changeworkorder = request.GET.get('workorder')
    customer = request.GET.get('customer')
    contact = request.GET.get('contact')
    print(contact)
    print(customer)
    #workorder = Workorder.objects.get(id=changeworkorder)
    if contact:
        contact = Contact.objects.filter(id=contact)
    else:
        contact = Contact.objects.filter(customer_id=customer).first
    if contact:
        print('hello')
        context = { 'contact': contact,
                    'cust':customer,
                    }
        return render(request, 'customers/partials/details_contact_info.html', context)
    else:
        print('hello2')
        contact = ''
        context = { 'contact': contact,
                    'cust':customer,
                    }
        return render(request, 'customers/partials/details_contact_info.html', context)


@login_required
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
            if not workorder:
                return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
            contact = Workorder.objects.get(id=workorder)
            contact = contact.contact_id
        obj = get_object_or_404(Contact, id=contact)
        form = ContactForm(instance=obj)
        context = {
            'form': form,
            'contact': contact
        }
    return render(request, 'customers/modals/edit_contact.html', context)

@login_required
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
        try:
            obj = Workorder.objects.get(id=workorder)
            obj.contact_id = contact
            obj.save(update_fields=['contact_id'])
            print('here')
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
        except:
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
    print(customer)
    #print(workorder)
    obj = Contact.objects.filter(customer=customer)
    context = {
        'obj': obj,
        'workorder': workorder
    }
    return render(request, 'customers/modals/change_contact.html', context)

@login_required
def customer_notes(request, pk=None):
    #pk = request.GET.get('customer')
    item = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        id = request.POST.get('id')
        print(id)
        item = get_object_or_404(Customer, id=id)
        form = CustomerNoteForm(request.POST, instance=item)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
        else:
            print(form.errors)
    form = CustomerNoteForm(instance=item)
    context = {
        #'notes':notes,
        'form':form,
        'pk': pk,
    }
    return render(request, 'customers/modals/notes.html', context) 

@login_required
def detail(request, id=None):
    customer = Customer.objects.get(id=id)
    history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).order_by("-workorder")[:5]
    context = {
            'customer': customer,
            'history': history,
        }
    return render(request, "customers/detail.html", context)

@login_required
def dashboard(request):
    customers = Customer.objects.all()
    context = {
        'customers':customers,
    }
    return render(request, "customers/dashboard.html", context)

@login_required
def expanded_detail(request, id=None):
    if not id:
        id = request.GET.get('customers')
        search = 0
    else:
        search = 1
    customers = Customer.objects.all()
    print(id)
    if id:
        aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
        today = timezone.now()
        for x in aging:
            if not x.date_billed:
                x.date_billed = today
            age = x.date_billed - today
            age = abs((age).days)
            print(type(age))
            Workorder.objects.filter(pk=x.pk).update(aging = age)
        
        customer = Customer.objects.get(id=id)
        cust = customer.id
        history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).order_by("-workorder")[:5]
        workorder = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=1).exclude(quote=1).order_by("-workorder")[:25]
        completed = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
        quote = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
        balance = Workorder.objects.filter(customer_id=customer).exclude(quote=1).aggregate(Sum('total_balance'))
        current = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
        thirty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
        sixty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
        ninety = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
        onetwenty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
        #current = list(current.values())[0]
        #current = round(current, 2)


        context = {
            'workorders': workorder,
            'completed': completed,
            'quote': quote,
            'cust': cust,
            'customers':customers,
            'customer': customer,
            'history': history,
            'balance': balance,
            'current':current,
            'thirty':thirty,
            'sixty':sixty,
            'ninety':ninety,
            'onetwenty':onetwenty,
        }
        if search:
            return render(request, "customers/search_detail.html", context)
        else:
            return render(request, "customers/partials/details.html", context)