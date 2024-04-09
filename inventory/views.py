from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from .forms import AddVendorForm, AddInventoryItemForm
from .models import Vendor
from inventory.models import Inventory

# Create your views here.

@login_required
def list(request):
    pass

@login_required
def add_vendor(request):
    form = AddVendorForm()
    if request.htmx:
        if request.method == "POST":
            form = AddVendorForm(request.POST)
            pk = request.POST.get('item')
            cat = request.POST.get('cat')
            if form.is_valid():
                form.save()
                context = {
                    'pk': pk,
                    'cat': cat,
                }
                return redirect('workorders:edit_orderout_item', pk=pk, cat=cat)
        pk = request.GET.get('item')
        cat = request.GET.get('cat')
        print(pk)
        print(cat)
        context = {
                'form': form,
                'pk': pk,
                'cat': cat,
                #'categories': categories
            }
        return render (request, "inventory/vendors/add_vendor_modal.html", context)
    if request.method == "POST":
        form = AddVendorForm(request.POST)
        if form.is_valid():
            form.save()
        vendor = Vendor.objects.all()
        context = {
            'vendor': vendor,
        }
        return render (request, "inventory/vendors/list.html", context)
    context = {
        'form': form,
        #'categories': categories
    }
    return render (request, "inventory/vendors/add_vendor.html", context)


@login_required
def vendor_list(request):
    vendor = Vendor.objects.all().order_by("name")
    print('vendors')
    context = {
        'vendors': vendor,
    }
    return render(request, 'inventory/vendors/list.html', context)

@login_required
def detail(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    context = {
        'vendor': vendor,
    }
    return render(request, 'inventory/vendors/detail.html', context)

@login_required
def add_inventory_item(request):
    form = AddInventoryItemForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            #updated = timezone.now()
            if form.is_valid():
                item = request.POST.get('item')
                obj = form.save(commit=False)
                price_per_m = obj.price_per_m
                price_per_m = float(price_per_m)
                price_per_m = Decimal.from_float(price_per_m)
                price_per_m = round(price_per_m, 2)
                print(obj.invoice_date)
                #price_per_m = int(price_per_m)
                price_ea = price_per_m / 1000
                print(price_per_m)
                print(price_ea)
                #item = get_object_or_404(Inventory, pk=test)
                #print (item.name)
                #obj.save()
                Inventory.objects.filter(pk=item).update(price_per_m=price_per_m, unit_cost=price_ea, updated=obj.invoice_date)


                #messages.success(request, "Record Added...")
                return redirect('inventory:add_inventory_item')
        return render(request, 'inventory/items/add_inventory_item.html', {'form':form})
    else:
        messages.success(request, "You must be logged in")
        return redirect('home')