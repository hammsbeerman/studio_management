from django.shortcuts import render, redirect, get_object_or_404
from .forms import AddVendorForm
from .models import Vendor

# Create your views here.

def list(request):
    pass

def add_vendor(request):
    form = AddVendorForm()
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


def vendor_list(request):
    vendor = Vendor.objects.all()
    print('vendors')
    context = {
        'vendors': vendor,
    }
    return render(request, 'inventory/vendors/list.html', context)

def detail(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    context = {
        'vendor': vendor,
    }
    return render(request, 'inventory/vendors/detail.html', context)