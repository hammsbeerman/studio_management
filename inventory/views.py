from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from decimal import Decimal
from .forms import AddVendorForm, AddInventoryItemForm
from .models import Vendor, Inventory
from .serializers import InventorySerializer
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
    item = Inventory.objects.all().order_by('name')
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
                obj.save()
                Inventory.objects.filter(pk=item).update(price_per_m=price_per_m, unit_cost=price_ea, updated=obj.invoice_date)
            else:
                print(form.errors)


                #messages.success(request, "Record Added...")
            form = AddInventoryItemForm()
            item = Inventory.objects.all().order_by('name')
            context = {
                'form':form,
                'item':item
            }
            #return redirect('inventory:add_inventory_item', context)
            return render(request, 'inventory/items/add_inventory_item.html', context)

        context = {
            'form':form,
            'item':item
        }
        return render(request, 'inventory/items/add_inventory_item.html', context)
    else:
        messages.success(request, "You must be logged in")
        return redirect('home')


#Below this is solely for testing API data

#For testing serializer
#@api_view(['GET', 'POST'])
def inventory_list(request):
    if request.method == 'GET':
        inventory = Inventory.objects.all()
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


class InventoryCreate(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

class InventoryPRUD(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    lookup_field = "pk"

class InventoryListAPIView(generics.ListAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

class InventoryDetailAPIView(generics.RetrieveAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer