import os
import datetime
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Min, Sum, F, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from .models import Customer, Contact, ShipTo, MailingCustomer
from .forms import CustomerForm, ContactForm, CustomerNoteForm, ShipToForm, MailingCustomerForm
from controls.models import Numbering
from finance.models import Payments
from workorders.forms import WorkorderForm
from workorders.models import Workorder


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
    #history = Workorder.objects.filter(customer_id=customer).order_by("-workorder")[:10].exclude(workorder=1111)
    history = Workorder.objects.filter(customer_id=customer).order_by("-workorder")[:20]
    context = {
        'customer': customer,
        'contacts': contact,
        'history': history,
        }
    #print(contacts)
    return render(request, 'customers/partials/contacts.html', context)


@login_required
def customers(request):
    #customer = Customer.objects.all().order_by('company_name')
    customer = Customer.objects.filter(active=1).order_by('company_name')
    context = {
        'customers': customer
        }
    print(customer)
    #print(contacts)
    return render(request, 'customers/partials/customers.html', context)

#This is a duplicate, not sure what this does
# @login_required
# def customer_list(request):
#     customer = Customer.objects.all().order_by('company_name')
#     context = {
#         'customers': customer
#         }
#     return render(request, 'customers/list.html', context)


# @login_required
# def new_customer(request):
#     if request.method == "POST":
#         form = CustomerForm(request.POST, request.FILES)
#         print("FILES:", request.FILES)
#         c = request.POST.get('customer')
#         cn = request.POST.get('company_name')
#         fn = request.POST.get('first_name')
#         ln = request.POST.get('last_name')
#         print('customer?')
#         print(c)
#          # check if a new file was uploaded
#         if request.FILES.get("tax_exempt_paperwork"):
#             uploaded_file = request.FILES["tax_exempt_paperwork"]

#             # build new filename
#             base, ext = os.path.splitext(uploaded_file.name)
#             if not cn:
#                 print('Empty string') 
#                 print(fn)
#                 print(ln)
#                 form.instance.company_name = fn + ' ' + ln
#                 cn = form.instance.company_name
#                 #print(obj.company_name)
#                 new_name = f"{cn}_{base}{ext}"
#                 # assign new name
#                 uploaded_file.name = new_name
#             if cn:
#                 print(cn)
#                 new_name = f"{cn}_{base}{ext}"
#                 # assign new name
#                 uploaded_file.name = new_name
#         if form.is_valid():
#             ##Increase workorder numbering
#             n = Numbering.objects.get(pk=2)
#             form.instance.customer_number = n.value
#             #workorder = n.value
#             inc = int('1')
#             n.value = n.value + inc
#             print(n.value)
#             #n.save() -- Save in the if statement below
#             ## End of numbering
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
#                 n.save()
#                 #return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
#             else:
#                 print(cn)
#                 form.save()
#                 n.save()
#                 #return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
#             print('customer stuff')
#             newcust = form.instance.pk
#             print(form.instance.pk)
#             print(newcust)
#             customer = Customer.objects.get(pk=newcust)
#             print(customer)
#             #Add customer info to shipto database
#             shipto = ShipTo()
#             shipto.customer_id = newcust
#             shipto.company_name = customer.company_name
#             shipto.first_name = customer.first_name
#             shipto.last_name = customer.last_name
#             shipto.address1 = customer.address1
#             shipto.address2 = customer.address2
#             shipto.city = customer.city
#             shipto.state = customer.state
#             shipto.zipcode = customer.zipcode
#             shipto.phone1 = customer.phone1
#             shipto.phone2 = customer.phone2
#             shipto.email = customer.email
#             shipto.website = customer.website
#             shipto.logo = customer.logo
#             shipto.notes = customer.notes
#             shipto.active = customer.active
#             shipto.save()
#             print('Saved')
#             # obj.save
#             # form.save()
#             return HttpResponse(status=204, headers={'HX-Trigger': 'CustomerAdded'})
#     else:
#         form = CustomerForm()
#     return render(request, 'customers/modals/newcustomer_form.html', {
#         'form': form,
#     })

@login_required
def new_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST, request.FILES)
        # Normalize names once
        cn = (request.POST.get('company_name') or "").strip()
        fn = (request.POST.get('first_name') or "").strip()
        ln = (request.POST.get('last_name') or "").strip()

        # Rename uploaded tax-exempt file to include company/person name
        if request.FILES.get("tax_exempt_paperwork"):
            uploaded = request.FILES["tax_exempt_paperwork"]
            base, ext = os.path.splitext(uploaded.name)
            display_name = cn or f"{fn} {ln}".strip() or "customer"
            new_name = f"{slugify(display_name)}_{slugify(base)}{ext}"
            uploaded.name = new_name

        if form.is_valid():
            # require at least a company name or a person name
            if not (cn or fn or ln):
                return render(request, "customers/modals/newcustomer_form.html", {
                    "message": "Please fill in Company name or Customer Name",
                    "form": form,
                })

            # If no company_name, synthesize from first/last
            if not cn:
                form.instance.company_name = f"{fn} {ln}".strip()

            # Safe numbering: seed if missing, increment atomically
            # with transaction.atomic():
            #     num, _ = Numbering.objects.select_for_update().get_or_create(
            #         id=2,
            #         defaults=dict(name="Customer", prefix="C", padding=5, value=1),
            #     )
            #     next_num = num.value
            #     Numbering.objects.filter(pk=num.pk).update(value=F("value") + 1)

            # form.instance.customer_number = next_num

            # --- numbering (works regardless of Numbering fields) ---
            with transaction.atomic():
                NumberingModel = Numbering
                field_names = {
                    f.name for f in NumberingModel._meta.get_fields()
                    if getattr(f, "concrete", False) and not getattr(f, "auto_created", False)
                }

                defaults = {}
                if "name" in field_names: defaults["name"] = "Customer"
                if "value" in field_names: defaults["value"] = 1
                elif "current" in field_names: defaults["current"] = 1
                if "prefix" in field_names: defaults["prefix"] = "C"
                if "padding" in field_names: defaults["padding"] = 5

                num, _ = NumberingModel.objects.select_for_update().get_or_create(
                    id=2, defaults=defaults
                )

                counter_field = "value" if "value" in field_names else ("current" if "current" in field_names else None)
                next_num = getattr(num, counter_field) if counter_field else 1
                if counter_field:
                    NumberingModel.objects.filter(pk=num.pk).update(**{counter_field: F(counter_field) + 1})

            form.instance.customer_number = next_num
            # --- end numbering ---
            form.save()

            # Mirror to ShipTo
            customer = form.instance
            ShipTo.objects.create(
                customer=customer,
                company_name=customer.company_name,
                first_name=customer.first_name,
                last_name=customer.last_name,
                address1=customer.address1,
                address2=customer.address2,
                city=customer.city,
                state=customer.state,
                zipcode=customer.zipcode,
                phone1=customer.phone1,
                phone2=customer.phone2,
                email=customer.email,
                website=customer.website,
                logo=customer.logo,
                notes=customer.notes,
                active=customer.active,
            )

            return HttpResponse(status=204, headers={"HX-Trigger": "CustomerAdded"})
    else:
        form = CustomerForm()

    return render(request, "customers/modals/newcustomer_form.html", {"form": form})

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
        print("FILES:", request.FILES)
        c = request.POST.get('customer')
        cn = request.POST.get('company_name')
        fn = request.POST.get('first_name')
        ln = request.POST.get('last_name')
        print('customer?')
        print(c)
         # check if a new file was uploaded
        if request.FILES.get("tax_exempt_paperwork"):
            uploaded_file = request.FILES["tax_exempt_paperwork"]

            # build new filename
            base, ext = os.path.splitext(uploaded_file.name)
            if not cn:
                print('Empty string') 
                print(fn)
                print(ln)
                form.instance.company_name = fn + ' ' + ln
                cn = form.instance.company_name
                #print(obj.company_name)
                new_name = f"{cn}_{base}_{obj.id}{ext}"
                # assign new name
                uploaded_file.name = new_name
            if cn:
                print(cn)
                new_name = f"{cn}_{base}_{obj.id}{ext}"
                # assign new name
                uploaded_file.name = new_name

        if form.is_valid():
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
    print('test')
    if request.htmx:
        print('htmx')
        changeworkorder = request.GET.get('workorder')
        changecustomer = request.GET.get('customer')
        workorder = Workorder.objects.get(id=changeworkorder)
        contact = workorder.contact_id
        shipto = workorder.ship_to_id
        print(contact)
        print('somethingfadasda')
        print('shipto')
        print(shipto)
        print('testing')
        if contact:
            print(contact)
            print('test')
            contact = Contact.objects.get(id=contact)
            print(contact.id)
            if shipto:
                shipto = ShipTo.objects.get(id=shipto)
            else:
                shipto = ''
            context = { 
                'contact': contact,
                'changecustomer':changecustomer,
                'changeworkorder':changeworkorder,
                'shipto':shipto
                }
            return render(request, 'customers/partials/contact_info.html', context)
        if shipto:
            shipto = ShipTo.objects.get(id=shipto)
            if contact:
                contact = Contact.objects.get(id=contact)
            else:
                contact = ''
            context = { 
                'contact': contact,
                'changecustomer':changecustomer,
                'changeworkorder':changeworkorder,
                'shipto':shipto
                }
            return render(request, 'customers/partials/contact_info.html', context)
        workorder = request.GET.get('workorder')
        print('workorder')
        print(workorder)
        contact = Workorder.objects.get(id=workorder)
        print(contact.contact_id)
        print('Shipto')
        print(contact.ship_to_id)
        contact = contact.contact_id
        #shipto = contact.ship_to_id
        print(contact)
        print('shipto')
        print(shipto)   
        #try:
        #contacts = Contact.objects.get(id=contact)
        try:
            shipto = ShipTo.objects.get(id=shipto)
        except ShipTo.DoesNotExist:
            shipto = None
        
        #except:
        #    pass
        print('testing')
        context = { 
            #'contacts': contacts,
            'shipto': shipto,
                   }
        return render(request, 'customers/partials/contact_info.html', context)
    workorder = Workorder.objects.get(workorder=id)
    if workorder.contact_id:
        contact = Contact.objects.get(id=workorder.contact_id)
    else: 
        contact = ''
    if workorder.ship_to_id:
        shipto = ShipTo.objects.get(id=workorder.ship_to_id)
    else:
        shipto = ''
    print('testing')
    context = {
            'shipto': shipto,
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
    """
    Customer dashboard details.

    - If called via HTMX (dropdown change), returns the partial
      templates/customers/partials/details.html (swapped into #customers)
    - If called as a normal page load with /customers/dashboard/details/<id>/,
      also renders the same partial (works fine as a full page too).
    """
    customer_id = id or request.GET.get("customers")
    customers = Customer.objects.only("id", "company_name").order_by("company_name")

    if not customer_id:
        return render(request, "customers/partials/details.html", {"customers": customers})

    customer = get_object_or_404(Customer, id=customer_id)

    # optional "primary" contact (safe)
    contact = (
        Contact.objects.filter(customer_id=customer.id)
        .only("id")
        .order_by("-id")
        .first()
    )

    base = (
        Workorder.objects
        .filter(customer_id=customer.id)
        .exclude(workorder=1111)
        .exclude(void=1)
        .select_related("workorder_status")
    )

    # keep fields tight but include what template touches
    base_fields = (
        "id",
        "workorder",
        "description",
        "created",
        "date_completed",
        "workorder_total",
        "total_balance",
        "open_balance",
        "billed",
        "paid_in_full",
        "aging",
        "quote",
        "void",
        "completed",
        "workorder_status",
        "workorder_status__icon",
    )

    history = (
        base.exclude(workorder=customer_id)  # preserving your legacy logic
            .order_by("-workorder")
            .only(*base_fields)[:5]
    )

    workorders = (
        base.exclude(completed=1, quote=1, void=1)
            .order_by("-workorder")
            .only(*base_fields)[:25]
    )

    # cap these so big customers don't time out
    completed = (
        base.filter(completed=1)
            .exclude(quote=1)
            .order_by("-workorder")
            .only(*base_fields)[:200]
    )

    quote = (
        base.filter(quote=1)
            .order_by("-workorder")
            .only(*base_fields)[:100]
    )

    # quick overall balance
    balance = base.exclude(quote=1).aggregate(
        balance=Coalesce(Sum("total_balance"), Decimal("0.00"))
    )

    # Aging buckets (DateField-friendly, no __date lookup)
    today = timezone.localdate()
    d30 = today - timedelta(days=30)
    d60 = today - timedelta(days=60)
    d90 = today - timedelta(days=90)
    d120 = today - timedelta(days=120)

    ar_base = base.filter(billed=1, paid_in_full=0).exclude(quote=1).exclude(void=1)

    buckets = ar_base.aggregate(
        current=Coalesce(Sum("open_balance", filter=Q(date_billed__gte=d30)), Decimal("0.00")),
        thirty=Coalesce(Sum("open_balance", filter=Q(date_billed__lt=d30, date_billed__gte=d60)), Decimal("0.00")),
        sixty=Coalesce(Sum("open_balance", filter=Q(date_billed__lt=d60, date_billed__gte=d90)), Decimal("0.00")),
        ninety=Coalesce(Sum("open_balance", filter=Q(date_billed__lt=d90, date_billed__gte=d120)), Decimal("0.00")),
        onetwenty=Coalesce(Sum("open_balance", filter=Q(date_billed__lt=d120)), Decimal("0.00")),
    )

    payments = (
        Payments.objects
        .filter(customer_id=customer.id)
        .exclude(void=1)
        .select_related("payment_type")
        .order_by("-date")
        .only("id", "date", "amount", "memo", "payment_type", "check_number", "giftcard_number")[:200]
    )

    context = {
        "customers": customers,
        "customer": customer,
        "cust": customer.id,
        "contact": contact,

        "history": history,
        "workorders": workorders,
        "completed": completed,
        "quote": quote,

        "balance": balance,

        # keep your legacy keys the finance partial expects
        "current": {"open_balance__sum": buckets["current"]},
        "thirty": {"open_balance__sum": buckets["thirty"]},
        "sixty": {"open_balance__sum": buckets["sixty"]},
        "ninety": {"open_balance__sum": buckets["ninety"]},
        "onetwenty": {"open_balance__sum": buckets["onetwenty"]},

        "payments": payments,
    }

    return render(request, "customers/partials/details.html", context)
        
@login_required
def edit_shipto(request):
    shipto = request.GET.get('shipto')
    #customer = request.GET.get('customer')
    if request.method == "POST":
        shipto_num = request.POST.get("shipto")
        obj = get_object_or_404(ShipTo, pk=shipto_num)
        #obj = (Contact, pk=contact_num)
        form = ShipToForm(request.POST, instance=obj)
        if form.is_valid():
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
    else:
        if not shipto:
            workorder = request.GET.get('workorder')
            if not workorder:
                return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
            shipto = Workorder.objects.get(id=workorder)
            shipto = shipto.ship_to_id
        obj = get_object_or_404(ShipTo, id=shipto)
        form = ShipToForm(instance=obj)
        context = {
            'form': form,
            'shipto': shipto
        }
    return render(request, 'customers/modals/edit_shipto.html', context)

@login_required
def new_shipto(request):
    customer = request.GET.get('customer')
    workorder = request.GET.get('workorder')
    print('customer')
    print(customer)
    print('workorder')
    print(workorder)
    if request.method == "POST":
        form = ShipToForm(request.POST)
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
                    Workorder.objects.filter(pk=workorder).update(ship_to_id=contact)
                except:
                    return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
                #obj = get_object_or_404(Workorder, pk=workorder)
                #form2 = 
                print(form.instance.id)
                print('else')
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
            
    else:
        form = ShipToForm()
        context = {
            'form': form,
            'customer': customer,
            'workorder': workorder
        }
    return render(request, 'customers/modals/newshipto_form.html', context)

@login_required
def change_shipto(request):
    customer = request.GET.get('customer')
    workorder = request.GET.get('workorder')
    if request.method == "POST":
        shipto = request.POST.get('shipto')
        workorder = request.POST.get('workorder')
        #obj = get_object_or_404(Workorder, pk=workorder)
        #form = WorkorderForm
        print(shipto)
        print(workorder)
        try:
            obj = Workorder.objects.get(id=workorder)
            obj.ship_to_id = shipto
            obj.save(update_fields=['ship_to_id'])
            print('here')
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
        except:
            return HttpResponse(status=204, headers={'HX-Trigger': 'ContactChanged'})
    print(customer)
    #print(workorder)
    obj = ShipTo.objects.filter(customer=customer)
    context = {
        'obj': obj,
        'workorder': workorder
    }
    return render(request, 'customers/modals/change_shipto.html', context)

def customer_list(request, customer=None):
    print(customer)
    mailing=''
    if customer == 'LK':
        workorders = Workorder.objects.all().exclude(quote=1).exclude(internal_company='Krueger Printing').exclude(internal_company='Office Supplies').order_by("customer_id", "-updated")
        old_workorders = Workorder.objects.all().exclude(quote=1).exclude(internal_company='Krueger Printing').exclude(internal_company='Office Supplies').exclude(date_completed__lt=datetime.now()-timedelta(days=90)).order_by("customer_id", "-updated")
        company = 'LK Design'
        # print(1)
        # print(workorders)
    if customer == 'K':
        workorders = Workorder.objects.all().exclude(quote=1).exclude(internal_company='LK Design').order_by("customer_id", "-updated")
        old_workorders = Workorder.objects.all().exclude(quote=1).exclude(internal_company='LK Design').exclude(date_completed__lt=datetime.now()-timedelta(days=90)).order_by("customer_id", "-updated")
        company = 'Krueger Printing'
        # print(2)
        # print(workorders)
    if customer == 'M':
        mailing = MailingCustomer.objects.all()
        workorders = ''
        company = 'Mailing List Add-ons'
    if customer == 'A' or not customer:
        workorders = Workorder.objects.all().exclude(quote=1).order_by("customer_id", "-updated")
        old_workorders = Workorder.objects.all().exclude(quote=1).exclude(date_completed__lt=datetime.now()-timedelta(days=90)).order_by("customer_id", "-updated")
        company = 'All'
        mailing = MailingCustomer.objects.all()
        # print(3)
        # print(workorders)
    unique_list = []
    list = []
    # old_workorder_list = []
    #print(old_workorders)
    for x in workorders:
        if x.customer not in list:
            # item = Workorder.objects.get(customer=x.customer).order_by('-date_billed')[:1]
            # x.last_date = item.date_billed
            # print(x.last_date)
            # print('item')
            # print(item)
            unique_list.append(x)
            list.append(x.customer)
    for x in mailing:
        print(x.company_name)
    # for x in unique_list:
    #     item = Workorder.objects.all()
    #     print(item.hr_customer)
    #     x.old = 1
    #     if x.customer.last_workorder:
    #         delta=datetime.today() - x.customer.last_workorder
    #         if delta.days > 2:
    #             x.old=True
    #         else:
    #             x.old=False
            # else:
            #     x.old=False
            # if x.customer.older_ninety:
            #     print('older')
            #     #old_workorder_list.append(x)
    # for x in unique_list:
    #     print(x.old)
    old_wo_unique_list = []
    # old_wo_list = []
    # for x in old_workorders:
    #     if x.date_completed:
    #         if x.customer not in old_wo_list:
    #             old_wo_unique_list.append(x)
    #             old_wo_list.append(x.customer)
    # print(old_wo_unique_list)
    # for x in old_wo_unique_list:
    #     print(x.date_completed)
    #print(unique_list.id)
    context = {
        #'workorders':workorders,
        'mailing':mailing,
        'old_wo_unique_list':old_wo_unique_list,
        'unique_list': unique_list,
        'company': company,
    }
    if customer:
        return render(request, 'customers/partials/customer_list.html', context)
    return render(request, 'customers/customer_list.html', context)

@login_required
def add_mailing_customer(request):
    if request.method == "POST":
        form = MailingCustomerForm(request.POST)
        if form.is_valid():
            cn = request.POST.get('company_name')
            fn = request.POST.get('first_name')
            ln = request.POST.get('last_name')
            if not cn and not fn and not ln:
                message = 'Please fill in Company name or Customer Name'
                context = {
                    'message': message,
                    'form': form
                }
                return redirect ('customers:add_mailing_customer')
            if not cn:
                print('Empty string')
                print(fn)
                print(ln)
                form.instance.company_name = fn + ' ' + ln
                form.save()
            else:
                print(cn)
                form.save()
            return redirect ('customers:add_mailing_customer')
    mailing_customer = MailingCustomer.objects.all()
    form = MailingCustomerForm()
    context = {
        'form': form,
        'mailing_customer': mailing_customer
    }
    return render(request, 'customers/add_mailing_customer.html', context)


def edit_mailing_customer(request, mailing=None):
    pk=mailing
    if request.method == "POST":
        instance = MailingCustomer.objects.get(id=pk)
        form = MailingCustomerForm(request.POST or None, instance=instance)
        if form.is_valid():
            cn = request.POST.get('company_name')
            fn = request.POST.get('first_name')
            ln = request.POST.get('last_name')
            if not cn and not fn and not ln:
                message = 'Please fill in Company name or Customer Name'
                context = {
                    'message': message,
                    'form': form
                }
                return redirect ('customers:add_mailing_customer')
            if not cn:
                print('Empty string')
                print(fn)
                print(ln)
                form.instance.company_name = fn + ' ' + ln
                form.save()
            else:
                print(cn)
                form.save()
            #InvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
            
            return redirect ('customers:add_mailing_customer') 
            #return HttpResponse(status=204, headers={'HX-Trigger': 'itemChanged'})         
        else:        
            messages.success(request, "Something went wrong")
            return redirect ('customers:add_mailing_customer')
    obj = get_object_or_404(MailingCustomer, id=mailing)
    form = MailingCustomerForm(instance=obj)
    # bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
    # vendors = Vendor.objects.all()
    mailing_customer = MailingCustomer.objects.all()
    context = {
        #'vendors':vendors,
        'pk':pk,
        #'bills':bills,
        'form':form,
        'mailing_customer':mailing_customer
    }
    return render (request, "customers/add_mailing_customer.html", context)

def delete_mailing_customer(request, mailing=None):
    MailingCustomer.objects.filter(id=mailing).delete()
    return redirect ('customers:add_mailing_customer') 

@login_required
def customer_edit_modal(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            # Tell HTMX to close modal + optionally refresh delivery table
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": "customerUpdated"
                }
            )
    else:
        form = CustomerForm(instance=customer)

    return render(
        request,
        "customers/modals/edit_customer.html",
        {"form": form, "customer": customer},
    )

@login_required
def customer_tab_open(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    qs = (Workorder.objects.filter(customer_id=customer.id)
          .exclude(workorder=1111)
          .exclude(completed=1, quote=1, void=1)
          .select_related("workorder_status")
          .order_by("-workorder"))

    page = Paginator(qs, 25).get_page(request.GET.get("page") or 1)
    return render(request, "customers/tabs/open.html", {"customer": customer, "page": page})

@login_required
def customer_tab_quotes(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    qs = (Workorder.objects.filter(customer_id=customer.id)
          .exclude(workorder=1111)
          .filter(quote=1)
          .select_related("workorder_status")
          .order_by("-workorder"))

    page = Paginator(qs, 25).get_page(request.GET.get("page") or 1)
    return render(request, "customers/tabs/quotes.html", {"customer": customer, "page": page})

@login_required
def customer_tab_completed(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    qs = (Workorder.objects.filter(customer_id=customer.id)
          .exclude(workorder=1111)
          .filter(completed=1)
          .exclude(quote=1)
          .order_by("-workorder"))

    page = Paginator(qs, 50).get_page(request.GET.get("page") or 1)
    return render(request, "customers/tabs/completed.html", {"customer": customer, "page": page})

@login_required
def customer_tab_payments(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    qs = (Payments.objects.filter(customer_id=customer.id)
          .exclude(void=1)
          .order_by("-date"))

    page = Paginator(qs, 50).get_page(request.GET.get("page") or 1)
    return render(request, "customers/tabs/payments.html", {"customer": customer, "page": page})











# @login_required
# def edit_mailing_customer(request):
#     if request.method == "POST":
#         form = MailingCustomerForm(request.POST)
#         if form.is_valid():
#             cn = request.POST.get('company_name')
#             fn = request.POST.get('first_name')
#             ln = request.POST.get('last_name')
#             if not cn and not fn and not ln:
#                 message = 'Please fill in Company name or Customer Name'
#                 context = {
#                     'message': message,
#                     'form': form
#                 }
#                 return render(request, 'customers/add_mailing_customer.html', context)
#             if not cn:
#                 print('Empty string')
#                 print(fn)
#                 print(ln)
#                 form.instance.company_name = fn + ' ' + ln
#                 form.save()
#             else:
#                 print(cn)
#                 form.save()
#     mailing_customer = MailingCustomer.objects.all()
#     form = MailingCustomerForm()
#     context = {
#         'form': form,
#         'mailing_customer': mailing_customer
#     }
#     return render(request, 'customers/add_mailing_customer.html', context)




# def cust_wo_address(request):
#     customer = Workorder.objects.all().order_by('hr_customer')
#     unique_list = []
#     list = []
#     for x in customer:
#         # check if exists in unique_list or not
#         if x.hr_customer not in list:
#             unique_list.append(x)
#             list.append(x.hr_customer)
#     print(unique_list)

#     context = {
#         'unique_list':unique_list,
#     }
#     return render (request, "controls/customers_without_address.html", context)

