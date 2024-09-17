from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from decimal import Decimal
from .forms import AddVendorForm
from .models import Vendor, InventoryQtyVariations, InventoryMaster
from .serializers import InventorySerializer
from finance.models import AllInvoiceItem, InvoiceItem
#from inventory.models import Inventory

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
        vendors = Vendor.objects.all().order_by('name')
        #print(vendor)
        context = {
            'vendors': vendors,
        }
        return render (request, "inventory/vendors/list.html", context)
    context = {
        'form': form,
        #'categories': categories
    }
    return render (request, "inventory/vendors/add_vendor.html", context)


@login_required
def vendor_list(request, vendor=None):
    if not vendor:
        vendor = Vendor.objects.all().order_by("name")
        print('vendors')
        context = {
            'vendors': vendor,
        }
        return render(request, 'inventory/vendors/list.html', context)
    else:
        if vendor == 'All':
            vendor = Vendor.objects.all().order_by("name")
        if vendor == 'Retail':
            vendor = Vendor.objects.filter(retail_vendor=1).order_by("name")
        elif vendor == 'Supply':
            vendor = Vendor.objects.filter(supplier=1).order_by("name")
        elif vendor == 'Inventory':
            vendor = Vendor.objects.filter(inventory_vendor=1).order_by("name")
        elif vendor == 'NonInventory':
            vendor = Vendor.objects.filter(non_inventory_vendor=1).order_by("name")
        elif vendor == 'Other':
            vendor = Vendor.objects.filter(supplier=0, retail_vendor=0, inventory_vendor=0, non_inventory_vendor=0).order_by("name")
        print('vendors')
        context = {
            'vendors': vendor,
        }
        return render(request, 'inventory/vendors/partials/vendor_list.html', context)

@login_required
def vendor_detail(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    if vendor.supplier == 1:
        supplier = 'True'
    else:
        supplier = 'False'
    if vendor.retail_vendor == 1:
        retail = 'True'
    else:
        retail = 'False'
    if vendor.inventory_vendor == 1:
        inventory_vendor = 'True'
    else:
        inventory_vendor = 'False'
    if vendor.non_inventory_vendor == 1:
        non_inventory_vendor = 'True'
    else:
        non_inventory_vendor = 'False'
    context = {
        'non_inventory_vendor': non_inventory_vendor,
        'inventory_vendor': inventory_vendor,
        'retail': retail,
        'supplier':supplier,
        'vendor': vendor,
    }
    return render(request, 'inventory/vendors/detail.html', context)

@login_required
def edit_vendor(request, id):
    if request.method == "POST":
        vendor = Vendor.objects.get(id=id)
        print(id)
        form = AddVendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
        vendors = Vendor.objects.all().order_by('name')
        #print(vendor)
        context = {
            'vendors': vendors,
        }
        return render (request, "inventory/vendors/list.html", context)
    obj = get_object_or_404(Vendor, id=id)
    form = AddVendorForm(instance=obj)
    vendor = id
    context = {
        'form':form,
        'vendor':vendor,
    }
    return render(request, 'inventory/vendors/edit_vendor.html', context)


def item_variations(request):
    items = InventoryQtyVariations.objects.all()
    unique_list = []
    list = []
    for x in items:
        # check if exists in unique_list or not
        if x.inventory not in list:
            unique_list.append(x)
            list.append(x.inventory)
    print(unique_list)
    context = {
        #'group':group,
        'unique_list':unique_list
    }
    return render(request, 'inventory/items/view_variations.html', context)

def item_variation_details(request, id=None):
    print(id)
    variations = InventoryQtyVariations.objects.filter(inventory=id)
    print(variations)
    context = {
        'variations':variations
    }
    return render(request, 'inventory/items/view_variation_details.html', context)

# def item_detail(request):
#     items = InventoryMaster.objects.all()
#     context = {
#         'items':items,
#     }
#     return render(request, 'inventory/items/item_details', context)

def item_details(request, id=None):
    item = request.GET.get('name')
    items = InventoryMaster.objects.all()
    print(item)
    if item:
        #item_history = AllInvoiceItem.objects.filter(internal_part_number=item)
        item_history = AccountsPayable.objects.filter(inter)
        print(item)
        context = {
            'item_history':item_history
        }
        return render (request, "inventory/items/partials/item_details.html", context)
    context = {
        'items':items,
    }
    return render(request, 'inventory/items/item_details.html', context)

































# @login_required
# def add_inventory_item(request):
#     form = AddInventoryItemForm(request.POST or None)
#     item = Inventory.objects.all().order_by('name')
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             #updated = timezone.now()
#             if form.is_valid():
#                 item = request.POST.get('item')
#                 obj = form.save(commit=False)
#                 price_per_m = obj.price_per_m
#                 price_per_m = float(price_per_m)
#                 price_per_m = Decimal.from_float(price_per_m)
#                 price_per_m = round(price_per_m, 2)
#                 print(obj.invoice_date)
#                 #price_per_m = int(price_per_m)
#                 price_ea = price_per_m / 1000
#                 print(price_per_m)
#                 print(price_ea)
#                 #item = get_object_or_404(Inventory, pk=test)
#                 #print (item.name)
#                 obj.save()
#                 Inventory.objects.filter(pk=item).update(price_per_m=price_per_m, unit_cost=price_ea, updated=obj.invoice_date)
#             else:
#                 print(form.errors)


#                 #messages.success(request, "Record Added...")
#             form = AddInventoryItemForm()
#             item = Inventory.objects.all().order_by('name')
#             context = {
#                 'form':form,
#                 'item':item
#             }
#             #return redirect('inventory:add_inventory_item', context)
#             return render(request, 'inventory/items/add_inventory_item.html', context)

#         context = {
#             'form':form,
#             'item':item
#         }
#         return render(request, 'inventory/items/add_inventory_item.html', context)
#     else:
#         messages.success(request, "You must be logged in")
#         return redirect('home')



















#Below this is solely for testing API data

#For testing serializer
#@api_view(['GET', 'POST'])
def inventory_list(request):
    if request.method == 'GET':
        inventory = InventoryMaster.objects.all()
        serializer = InventorySerializer(inventory, many=True)
        #return JsonResponse(serializer.data, safe=False)
        return JsonResponse({'inventory': serializer.data})
    if request.method == 'POST':
        #items = request.POST
        #print(items)
        serializer = InventorySerializer(data=request.data)
        #print(1)
        #print(serializer)
        if serializer.is_valid():
            #print(2)
            serializer.save()
            #print(3)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        
#def new_inventory_list(request)


# class InventoryCreate(generics.ListCreateAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

# class InventoryPRUD(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer
#     lookup_field = "pk"

# class InventoryListAPIView(generics.ListAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

# class InventoryDetailAPIView(generics.RetrieveAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

# class InventoryViewSet(viewsets.ModelViewSet):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer