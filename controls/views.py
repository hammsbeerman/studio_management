from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from .forms import SubCategoryForm, CategoryForm, AddSetPriceItemForm, AddSetPriceCategoryForm
from .models import SetPriceCategory, SubCategory, Category, SetPriceItemPrice
from workorders.models import Workorder
from customers.models import Customer, ShipTo
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    pass

@login_required
def add_category(request):
    form = CategoryForm()
    if request.method =="POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'CategoryListChanged'})
        else:
            print(form.errors)
    context = {
        'form': form,
    }
    return render (request, "pricesheet/modals/add_category.html", context)

@login_required
def add_subcategory(request):
    form = SubCategoryForm()
    category = Category.objects.all().exclude(active=0).order_by('name')
    if request.method =="POST":
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.category.setprice:
                form.save()
                pk = form.instance.pk
                subcat = SubCategory.objects.get(id=pk)
                subcat.set_price = 1
                subcat.setprice_name = obj.name
                subcat.save()
                print(obj.category)
                print(obj.category.id)
                lineitem = SetPriceCategory(category=obj.category, name=obj.name)
                lineitem.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ListChanged'})
            else:
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ListChanged'})
        else:
            print(form.errors)
    context = {
        'categories':category,
        'form': form,
    }
    return render (request, "pricesheet/modals/add_subcategory.html", context)

@login_required
def add_setprice_category(request):
    form = AddSetPriceCategoryForm()
    category = 3
    updated = timezone.now()
    if request.method =="POST":
        form = AddSetPriceCategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated = updated
            obj.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'CategoryAdded'})
        else:
            print(form.errors)
    context = {
        'form': form,
        'category':category,
    }
    return render (request, "pricesheet/modals/add_setprice_category.html", context)


@login_required
def add_setprice_item(request):
    form = AddSetPriceItemForm()
    updated = timezone.now()
    if request.method =="POST":
        form = AddSetPriceItemForm(request.POST)
        cat = 3
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated = updated
            obj.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'TemplateListChanged', 'category':'3'})
        else:
            print(form.errors)
    context = {
        'form': form,
    }
    return render (request, "pricesheet/modals/add_setprice_item.html", context)

# @login_required
# def setprice_list(request):
#     subcat = request.GET.get('subcat')
#     items = SetPriceItemPrice.objects.filter(name_id = subcat)
#     print(items)
#     context = {
#         'items':items
#     }
#     return render (request, "pricesheet/partials/setprice_list.html", context)

@login_required
def utilities(request):
    return render (request, "controls/utilities.html")


@login_required
def mark_all_verified(request):
    workorder = Workorder.objects.filter(completed=1)
    for x in workorder:
        print(x.workorder)
        Workorder.objects.filter(pk=x.pk).update(checked_and_verified=1)
    return render (request, "controls/utilities.html")

@login_required
def mark_all_invoiced(request):
    workorder = Workorder.objects.filter(completed=1).exclude(billed=0)
    for x in workorder:
        print(x.workorder)
        Workorder.objects.filter(pk=x.pk).update(invoice_sent=1)
    return render (request, "controls/utilities.html")

@login_required
def missing_workorders(request):
    if request.method =="POST":
        start = request.POST.get('start')
        end = request.POST.get('end')
        company = request.POST.get('company')
        try:
            start = int(start)
        except:
            return render (request, "controls/missing_workorders.html")
        try:
            end = int(end)
        except:
            return render (request, "controls/missing_workorders.html")
        workorders = list(range(start, end + 1))
        print(workorders)
        # max = workorders[0]
        # for i in workorders:
        #     #print(i)
        #     if i > max:
        #         max = i
        # print(max)
        #test = 3
        # if company == test:
        #     print('same')
        print(company)
        company = int(company)
        if company == 1:
            print('printleader')
            #xisting = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('kos_workorder', flat=True)
            existing = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('printleader_workorder', flat=True)
        elif company == 2:
            print('lk')
            #xisting = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('kos_workorder', flat=True)
            existing = Workorder.objects.filter(lk_workorder__isnull=False).values_list('lk_workorder', flat=True)
        elif company == 3:
            print('kos')
            #xisting = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('kos_workorder', flat=True)
            existing = Workorder.objects.filter(kos_workorder__isnull=False).values_list('printleader_workorder', flat=True)
        else:
            print('broken')
            return render (request, "controls/missing_workorders.html")
        exist = (list(existing))
        print(exist)
        try:
            cleaned = [eval(i) for i in exist]
        except:
            return render (request, "controls/missing_workorders.html")
        print(cleaned)

        set1 = set(workorders)
        set2 = set(cleaned)


        missing = list(sorted(set1 - set2))
        print('missing:', missing)
        context = {
            'missing':missing,
        }
        return render (request, "controls/missing_workorders.html", context)
    return render (request, "controls/missing_workorders.html")

@login_required
def update_complete_date(request):
    workorder = Workorder.objects.filter(completed=1)
    for x in workorder:
        print(x.workorder)
        date = x.updated
        print(date)
        Workorder.objects.filter(pk=x.pk).update(date_completed=date)
    return render (request, "controls/utilities.html")

def special_tools(request):
    return render (request, "controls/specialized_tools.html")

def customer_shipto(request):
    #index = 0
    #limit = 5
    customer = Customer.objects.all()
    for x in customer:
        company_name = x.company_name
        first_name = x.first_name
        last_name = x.last_name
        address1 = x.address1
        address2 = x.address2
        city = x.city
        state = x.state
        zipcode = x.zipcode
        phone1 = x.phone1
        phone2 = x.phone2
        email = x.email
        website = x.website
        logo = x.logo
        notes = x.notes
        active = x.active
        shipto = ShipTo()
        shipto.customer_id = x.pk
        shipto.company_name = company_name
        shipto.first_name = first_name
        shipto.last_name = last_name
        shipto.address1 = address1
        shipto.address2 = address2
        shipto.city = city
        shipto.state = state
        shipto.zipcode = zipcode
        shipto.phone1 = phone1
        shipto.phone2 = phone2
        shipto.email = email
        shipto.website = website
        shipto.logo = logo
        shipto.notes = notes
        shipto.active = active
        shipto.save()
        print('Saved')
        #index += 1
        #if index == limit:
        #    break
    return render (request, "controls/utilities.html")


def workorder_ship(request):
    # index = 0
    # limit = 5
    workorder = Workorder.objects.all()
    for x in workorder:
        customer = Customer.objects.get(pk=x.customer_id)
        cust = customer.id
        #pk = 203
        print(x.pk)
        print(x.workorder)
        print(customer.company_name)
        print('customer num')
        print(cust)
        shipto = ShipTo.objects.get(customer_id=cust)
        print(shipto.pk)
        ship = shipto.pk
        Workorder.objects.filter(pk=x.pk).update(ship_to_id=ship)
        # index += 1
        # if index == limit:
        #    break
        #shipto = ShipTo.objects.get(pk=customer.pk)
        #print(shipto)
        #shipto = ShipTo.objects.filter(customer=x.pk)
        #print(shipto)
        # print(x.pk)
        # pk = x.pk
        # pk = int(pk)
        # print(pk)
        # try:
        #     shipto = ShipTo.objects.get(customer=pk)
        #     print(shipto)
        # except:
        #     print(x.pk)
        #     print('Nope')
        



        # print(x.id)
        # try:
        #     shipto = ShipTo.objects.get(customer_id=x.id)
        #     print('sadasda')
        #     print(shipto.id)
        # except:
        #     pass






        # try:
        #     shipto = ShipTo.objects.get(customer=x.pk)
        #     ship = shipto.pk
        #     print(x.id)
        #     print(ship)
        #     Workorder.objects.filter(pk=x.pk).update(ship_to_id=ship)
        # except:
        #     pass
    return render (request, "controls/utilities.html")

def cust_history(request):
    customer = Workorder.objects.all().order_by('hr_customer')
    unique_list = []
    list = []
    for x in customer:
        # check if exists in unique_list or not
        if x.hr_customer not in list:
            unique_list.append(x)
            list.append(x.hr_customer)
    print(unique_list)

    context = {
        'unique_list':unique_list,
        'customer':customer
    }
    return render (request, "controls/workorder_history.html", context)

def cust_address(request):
    customer = Workorder.objects.all().order_by('hr_customer')
    unique_list = []
    list = []
    for x in customer:
        # check if exists in unique_list or not
        if x.hr_customer not in list:
            unique_list.append(x)
            list.append(x.hr_customer)
    print(unique_list)

    context = {
        'unique_list':unique_list,
    }
    return render (request, "controls/customers_with_address.html", context)

def cust_wo_address(request):
    customer = Workorder.objects.all().order_by('hr_customer')
    unique_list = []
    list = []
    for x in customer:
        # check if exists in unique_list or not
        if x.hr_customer not in list:
            unique_list.append(x)
            list.append(x.hr_customer)
    print(unique_list)

    context = {
        'unique_list':unique_list,
    }
    return render (request, "controls/customers_without_address.html", context)



