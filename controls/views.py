from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Max, Sum
from django.contrib import messages
from datetime import datetime
from .forms import SubCategoryForm, CategoryForm, AddSetPriceItemForm, AddSetPriceCategoryForm, AddInventoryPricingGroupForm
from .models import SetPriceCategory, SubCategory, Category
from workorders.models import Workorder
from customers.models import Customer, ShipTo
from inventory.models import Inventory, InventoryMaster, Vendor, VendorItemDetail, InventoryPricingGroup, InventoryQtyVariations
from controls.models import Measurement, GroupCategory
from finance.models import InvoiceItem, Araging, Krueger_Araging
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
            print(exist)
            cleaned = [eval(i) for i in exist if i.isdigit( )]
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

#Create master inventory item from items already in inventory list
def create_inventory_from_inventory(request):
    #inventory = Inventory.objects.all()[:120]
    inventory = Inventory.objects.all()
    print(inventory)
    for x in inventory:
        if not x.internal_part_number:
            name = x.name
            description = x.description
            p_vpn = x.vendor_part_number
            measurement = x.measurement
            unit_cost = x.unit_cost
            m = x.price_per_m
            if not unit_cost:
                unit_cost=0
            item = InventoryMaster(name=name, description=description, supplies=1, retail=1, primary_vendor_part_number=p_vpn, primary_base_unit=measurement, unit_cost=unit_cost, price_per_m=m)
            print(x.pk)
            item.save()
            print('saved')
            print(item.pk)
            ipn = Inventory.objects.filter(pk=x.pk).update(internal_part_number=item.pk)
            print('IPN')
            print(ipn)
            #Inventory.objects.filter(internal_part_number=instance.pk).update(unit_cost=unit_cost, price_per_m=m, updated=datetime.now())
    return render (request, "controls/specialized_tools.html")













def add_primary_vendor(request):
    if request.method =="POST":
        vendor = request.POST.get('vendor')
        id_list = request.POST.getlist('item')
        print(vendor)
        for x in id_list:
            InventoryMaster.objects.filter(pk=x).update(primary_vendor=vendor)
            i = InventoryMaster.objects.get(pk=x)
            n = InventoryMaster.objects.filter(pk=x)
            #print(n.id)
            print(i.name)
            item = VendorItemDetail(internal_part_number=InventoryMaster.objects.get(pk=x), vendor=i.primary_vendor, name=i.name, vendor_part_number=i.primary_vendor_part_number, description=i.description, supplies=i.supplies, retail=i.retail, non_inventory=i.non_inventory, created=datetime.now(), updated=datetime.now(), high_price=i.high_price)
            item.save()
    items = InventoryMaster.objects.all
    vendors = Vendor.objects.all().order_by('name')
    context = {
        'items':items,
        'vendors':vendors,
    }
    return render (request, "controls/add_primary_vendor.html", context)

def add_primary_baseunit(request):
    if request.method =="POST":
        unit = request.POST.get('unit')
        qty = request.POST.get('qty')
        #unit = int(unit)
        id_list = request.POST.getlist('item')
        print(unit)
        print(qty)
        for x in id_list:
            InventoryMaster.objects.filter(pk=x).update(primary_base_unit=unit, units_per_base_unit=qty)
            variation = InventoryQtyVariations(inventory=InventoryMaster.objects.get(pk=x), variation=Measurement.objects.get(id=unit), variation_qty=qty)
            #variation.variation = unit
            variation.save()
            print('variation')
            print(variation.pk)
            print('variation')
            #variation=Measurement.objects.get(pk=unit), variation_qty=100

            #This could be changed to add primary unit to vendor detail if needed
            # i = InventoryMaster.objects.get(pk=x)
            # n = InventoryMaster.objects.filter(pk=x)
            # #print(n.id)
            # print(i.name)
            # item = VendorItemDetail(internal_part_number=InventoryMaster.objects.get(pk=x), vendor=i.primary_vendor, name=i.name, vendor_part_number=i.primary_vendor_part_number, description=i.description, supplies=i.supplies, retail=i.retail, non_inventory=i.non_inventory, created=datetime.now(), updated=datetime.now(), high_price=i.high_price)
            # item.save()
    units = Measurement.objects.all
    items = InventoryMaster.objects.all
    context = {
        'items':items,
        'units':units,
    }
    return render (request, "controls/add_primary_baseunit.html", context)

def add_units_per_base_unit(request):
    if request.method =="POST":
        units = request.POST.get('qty')
        id_list = request.POST.getlist('item')
        print(units)
        for x in id_list:
            InventoryMaster.objects.filter(pk=x).update(units_per_base_unit=units)
    items = InventoryMaster.objects.all
    context = {
        'items':items,
    }
    return render (request, "controls/add_units_per_base_unit.html", context)


def view_price_groups(request):
    group = GroupCategory.objects.all().order_by('name')
    # group = InventoryPricingGroup.objects.all().order_by('group')
    # unique_list = []
    # list = []
    # for x in group:
    #     # check if exists in unique_list or not
    #     if x.group not in list:
    #         unique_list.append(x)
    #         list.append(x.group)
    # print(unique_list)
    context = {
        'group':group,
        #'unique_list':unique_list
    }
    return render (request, "controls/view_price_groups.html", context)


def view_price_group_detail(request, id=None):
    #print(id)
    group_id = GroupCategory.objects.get(pk=id)
    #item = InventoryMaster.objects.get(pk=51)
    #group = InventoryPricingGroup.objects.filter(inventory=item)
    group = InventoryPricingGroup.objects.filter(group=id)
    #print(group)
    #for x in group:
        #print(x)
        #print(x.id)
    context = {
        'group_id':group_id,
        'group':group
    }
    return render (request, "controls/view_price_group_detail.html", context)

def add_price_group(request):
    if request.method =="POST":
        group = request.POST.get('group_name')
        #obj = ItemPricingGroup(name=group)
        obj = GroupCategory(name=group)
        obj.save()
        return redirect ('controls:view_price_groups')
    return render (request, "controls/add_price_group.html")

def add_price_group_item(request, id=None, list=None):
    if id:
        group_id=id
    groups = GroupCategory.objects.all().order_by('name')
    items = InventoryMaster.objects.all()
    if list == 'all':
        items = InventoryMaster.objects.all()
    if list == 'nogroup':
        items = InventoryMaster.objects.filter(not_grouped=1)
    if list == 'group':
        items = InventoryMaster.objects.filter(grouped=1)
    notgrouped = request.POST.get('notgrouped')
    print(notgrouped)
    if request.method == "POST":
        notgrouped = request.POST.get('notgrouped')
        group_id = request.POST.get('group_id')
        if notgrouped:
            id_list = request.POST.getlist('item')
            for x in id_list:
                InventoryMaster.objects.filter(pk=x).update(not_grouped=1)
            context = {
                'group_id':group_id,
                'items':items,
                'groups':groups,
                #'form':form,
            }
            print(group_id)
            print(items)
            print(groups)
            return redirect ('controls:view_price_groups')
            #return render (request, "controls/add_price_group_item.html", context)
        # group = request.POST.get('group_id')
        #group_id = group
        #print(group)
        id_list = request.POST.getlist('item')
        for x in id_list:
            InventoryMaster.objects.filter(pk=x).update(grouped=1)
            item = InventoryMaster.objects.get(pk=x)
            group = GroupCategory.objects.get(pk=group_id)
            #obj = InventoryPricingGroup(inventory=InventoryMaster.objects.get(pk=x), group=ItemPricingGroup.objects.get(pk=group))
            obj = InventoryPricingGroup(inventory=item, group=group)
            try:
                unique = get_object_or_404(InventoryPricingGroup, inventory=item, group=group)
                print('exists')
            except:
                obj.save()
            groups = InventoryPricingGroup.objects.filter(inventory=item)
            for x in groups:
                #InventoryMaster.price_group.add(x.group)
                #Item comes from line 537
                item.price_group.add(x.group)
        return redirect('controls:view_price_group_detail', id=group_id)
    context = {
        'group_id':group_id,
        'items':items,
        'groups':groups,
        #'form':form,
    }
    if list == 'all':
        return render (request, "controls/partials/price_group_all.html", context)
    if list == 'nogroup':
        return render (request, "controls/partials/price_group_notgrouped.html", context)
    if list == 'group':
        return render (request, "controls/partials/price_group_grouped.html", context)
    return render (request, "controls/add_price_group_item.html", context)

def add_item_variation(request):
    #items = InventoryMaster.objects.all
    units = Measurement.objects.all()
    context = {
        #'items':items,
        'units':units,
    }
    return render (request, "controls/partials/add_item_variation.html", context )

def add_base_qty_variation(request):
    #items = InventoryMaster.objects.all()[:60]
    items = InventoryMaster.objects.all()
    for x in items:
        print(x.pk)
        variation = InventoryQtyVariations.objects.filter(inventory=x.pk)
        if variation:
            print('exists')
        else:
            if x.primary_base_unit and x.units_per_base_unit:
                print(x.primary_base_unit)
                print(x.units_per_base_unit)
                # base = x.primary_base_unit
                # unit = x.units_per_base_unit
                var = InventoryQtyVariations(inventory=InventoryMaster.objects.get(pk=x.pk), variation=Measurement.objects.get(id=x.primary_base_unit.id), variation_qty=x.units_per_base_unit)
                var.save()
    return redirect ('controls:utilities')

def add_internal_part_number(request):
    items = InvoiceItem.objects.all()


def get_highest_item_price(request):
    item = InventoryMaster.objects.filter(pk=201)
    for x in item:
        print(x.high_price)
        try:
            high_cost = InvoiceItem.objects.filter(internal_part_number=x.pk).aggregate(Max('unit_cost'))
            high_cost = list(high_cost.values())[0]
        except:
            print('error')
        if high_cost:
            InventoryMaster.objects.filter(pk=x.pk).update(high_price=high_cost)
            # Workorder.objects.filter(pk=x.pk).update(checked_and_verified=1)
        print(x.name)
        print(high_cost)
    item = InventoryMaster.objects.get(pk=201)
    print(item.high_price)


def items_missing_details(request):
    items = VendorItemDetail.objects.all()
    context = {
        'items':items,
    }
    return render (request, "controls/items_missing_details.html", context )


#Needs to be made into a cronjob
def high_price_item(request):
    items = InventoryMaster.objects.filter().exclude(non_inventory=1)
    for x in items:
        try:
            high_cost = InvoiceItem.objects.filter(internal_part_number=x.pk).aggregate(Max('unit_cost'))
            high_cost = list(high_cost.values())[0]
        except:
            high_cost = None
        if high_cost:
            print(x.name)
            print(high_cost)
            #InventoryMaster.objects.filter(pk=x.pk).update(high_price=high_cost)


# def vendor_children(request):
#     vendor = 


    
    # items = AllInvoiceItem.objects.all()
    # for x in items:
    #     y = x.invoice_item.internal_part_number
    #     z = y.primary_base_unit.id
    #     # print(y.id)
    #     # print(y.primary_base_unit.id)
    #     qty = x.qty
    #     unit_cost = x.unit_cost
    #     line = qty * unit_cost
    #     AllInvoiceItem.objects.filter(pk=x.pk).update(internal_part_number=InventoryMaster.objects.get(id=y.id), unit=Measurement.objects.get(id=z), line_total=line)
    # return redirect ('controls:utilities')
        




# def add_primary_vendor(request):
#     if request.method =="POST":
#         vendor = request.POST.get('vendor')
#         id_list = request.POST.getlist('item')
#         print(vendor)
#         for x in id_list:
#             InventoryMaster.objects.filter(pk=x).update(primary_vendor=vendor)
#             i = InventoryMaster.objects.get(pk=x)
#             n = InventoryMaster.objects.filter(pk=x)
#             #print(n.id)
#             print(i.name)
#             item = VendorItemDetail(internal_part_number=InventoryMaster.objects.get(pk=x), vendor=i.primary_vendor, name=i.name, vendor_part_number=i.primary_vendor_part_number, description=i.description, supplies=i.supplies, retail=i.retail, non_inventory=i.non_inventory, created=datetime.now(), updated=datetime.now(), high_price=i.high_price)
#             item.save()
#     items = InventoryMaster.objects.all
#     vendors = Vendor.objects.all
#     context = {
#         'items':items,
#         'vendors':vendors,
#     }
#     return render (request, "controls/add_primary_vendor.html", context)




#form = AddInventoryPricingGroupForm()


# @login_required
# def add_setprice_item(request):
#     form = AddSetPriceItemForm()
#     updated = timezone.now()
#     if request.method =="POST":
#         form = AddSetPriceItemForm(request.POST)
#         cat = 3
#         if form.is_valid():
#             obj = form.save(commit=False)
#             obj.updated = updated
#             obj.save()
#             return HttpResponse(status=204, headers={'HX-Trigger': 'TemplateListChanged', 'category':'3'})
#         else:
#             print(form.errors)
#     context = {
#         'form': form,
#     }
#     # return render (request, "pricesheet/modals/add_setprice_item.html", context)

@login_required
def krueger_statements(request):
    #Most of this function was moved to a cronjob
    update_ar = request.GET.get('up')
    print('update')
    print(update_ar)
    #customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
    today = timezone.now()
    customers = Customer.objects.all().order_by('company_name')
    # ar = Araging.objects.all()
    ar = Krueger_Araging.objects.filter
    workorders = Workorder.objects.filter().exclude(billed=0).exclude(internal_company='LK Design').exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).values('hr_customer').distinct()
    statement = Krueger_Araging.objects.filter(hr_customer__in=workorders)
    #workorders = Workorder.objects.filter(customer_id__in=need_statement)
    print(customers)
    for x in statement:
         print(f"ID: {x.customer.id}")
    #     if not x.date_billed:
    #         x.date_billed = today
    #     age = x.date_billed - today
    #     age = abs((age).days)
    #     print(age)
    #     Workorder.objects.filter(pk=x.pk).update(aging = age)
    total_balance = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    # for x in customers:
    #     try:
    #         #Get the Araging customer and check to see if aging has been updated today
    #         modified = Araging.objects.get(customer=x.id)
    #         print(x.company_name)
    #         day = today.strftime('%Y-%m-%d')
    #         day = str(day)
    #         date = str(modified.date)
    #         print(day)
    #         print(date)
    #         if day == date:
    #             #Don't update, as its been done today
    #             print('today')
    #             update = 0
    #             if update_ar == '1':
    #                 print('update')
    #                 update = 1
    #         else:
    #             update = 1
    #     except:
    #         update = 1
    #     #Update the Araging that needs to be done
    #     if update == 1:
    #         if Workorder.objects.filter(customer_id = x.id).exists():
    #             current = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
    #             try:
    #                 current = list(current.values())[0]
    #             except:
    #                 current = 0
    #             thirty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
    #             try: 
    #                 thirty = list(thirty.values())[0]
    #             except:
    #                 thirty = 0
    #             sixty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
    #             try:
    #                 sixty = list(sixty.values())[0]
    #             except:
    #                 sixty = 0
    #             ninety = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
    #             try:
    #                 ninety = list(ninety.values())[0]
    #             except:
    #                 ninety = 0
    #             onetwenty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
    #             try:
    #                 onetwenty = list(onetwenty.values())[0]
    #             except:
    #                 onetwenty = 0
    #             total = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    #             try:
    #                 total = list(total.values())[0]
    #             except:
    #                 total = 0
    #             try: 
    #                 obj = Araging.objects.get(customer_id=x.id)
    #                 Araging.objects.filter(customer_id=x.id).update(hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
    #             except:
    #                 obj = Araging(customer_id=x.id,hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
    #                 obj.save()
    ar = Krueger_Araging.objects.all().order_by('hr_customer')
    #total_current = Araging.objects.filter().aggregate(Sum('current'))
    total_current = ar.filter().aggregate(Sum('current'))
    total_thirty = ar.filter().aggregate(Sum('thirty'))
    total_sixty = ar.filter().aggregate(Sum('sixty'))
    total_ninety = ar.filter().aggregate(Sum('ninety'))
    total_onetwenty = ar.filter().aggregate(Sum('onetwenty'))
    print(total_current)
    
    #print(ar)
    context = {
        'total_current':total_current,
        'total_thirty':total_thirty,
        'total_sixty':total_sixty,
        'total_ninety':total_ninety,
        'total_onetwenty':total_onetwenty,
        'total_balance':total_balance,
        'ar': ar,
        'workorders': workorders,
        'statement': statement,
    }
    return render(request, 'finance/reports/krueger_statements.html', context)

def krueger_ar_aging(request):
    # update_ar = request.GET.get('up')
    # print('update')
    # print(update_ar)
    # #customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
    today = timezone.now()
    customers = Customer.objects.all().order_by('company_name')
    ar = Krueger_Araging.objects.all()
    workorders = Workorder.objects.filter().exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(internal_company='LK Design')
    for x in workorders:
        #print(x.id)
        if not x.date_billed:
            x.date_billed = today
        age = x.date_billed - today
        age = abs((age).days)
        print(age)
        Workorder.objects.filter(pk=x.pk).update(aging = age)
    total_balance = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
    for x in customers:
        # try:
        #     #Get the Araging customer and check to see if aging has been updated today
        #     modified = Araging.objects.get(customer=x.id)
        #     print(x.company_name)
        #     day = today.strftime('%Y-%m-%d')
        #     day = str(day)
        #     date = str(modified.date)
        #     print(day)
        #     print(date)
        #     if day == date:
        #         #Don't update, as its been done today
        #         print('today')
        #         update = 0
        #         if update_ar == '1':
        #             print('update')
        #             update = 1
        #     else:
        #         update = 1
        # except:
        #     update = 1
        #Update the Araging that needs to be done
        # if update == 1:
        if Workorder.objects.filter(customer_id = x.id).exists():
            print(x.id)
            current = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
            try:
                current = list(current.values())[0]
                print(current)
            except:
                current = 0
            thirty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
            try: 
                thirty = list(thirty.values())[0]
            except:
                thirty = 0
            sixty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
            try:
                sixty = list(sixty.values())[0]
            except:
                sixty = 0
            ninety = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
            try:
                ninety = list(ninety.values())[0]
            except:
                ninety = 0
            onetwenty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
            try:
                onetwenty = list(onetwenty.values())[0]
                print(onetwenty)
            except:
                onetwenty = 0
            total = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
            try:
                total = list(total.values())[0]
            except:
                total = 0
            try: 
                obj = Krueger_Araging.objects.get(customer_id=x.id)
                Krueger_Araging.objects.filter(customer_id=x.id).update(hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
                print(1)
            except:
                obj = Krueger_Araging(customer_id=x.id,hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
                obj.save()
                print(2)
    ar = Krueger_Araging.objects.all().order_by('hr_customer')
    #total_current = Araging.objects.filter().aggregate(Sum('current'))
    total_current = ar.filter().aggregate(Sum('current'))
    total_thirty = ar.filter().aggregate(Sum('thirty'))
    total_sixty = ar.filter().aggregate(Sum('sixty'))
    total_ninety = ar.filter().aggregate(Sum('ninety'))
    total_onetwenty = ar.filter().aggregate(Sum('onetwenty'))
    print(total_current)
    
    #print(ar)
    context = {
        'total_current':total_current,
        'total_thirty':total_thirty,
        'total_sixty':total_sixty,
        'total_ninety':total_ninety,
        'total_onetwenty':total_onetwenty,
        'total_balance':total_balance,
        'ar': ar
    }
    return render(request, 'finance/reports/krueger_statements.html', context)