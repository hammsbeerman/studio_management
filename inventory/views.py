from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import AddVendorForm
from .models import Vendor

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