from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from finance.models import AccountsPayable
from inventory.models import Vendor
from .forms import AddVendorForm


@login_required
def add_vendor(request):
    form = AddVendorForm()
    if request.method == "POST":
        form = AddVendorForm(request.POST)
        if form.is_valid():
            form.save()
        vendors = Vendor.objects.filter(retail_vendor=1).order_by("name")
        context = {"vendors": vendors}
        return render(request, "retail/vendors/list.html", context)

    context = {"form": form}
    return render(request, "retail/vendors/add_vendor.html", context)


@login_required
def vendor_list(request):
    vendors = Vendor.objects.filter(retail_vendor=1).order_by("name")
    context = {"vendors": vendors}
    return render(request, "retail/vendors/list.html", context)


@login_required
def vendor_detail(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    context = {"vendor": vendor}
    return render(request, "retail/vendors/detail.html", context)


@login_required
def invoice_list(request):
    invoices = AccountsPayable.objects.filter(retail_invoice=1).order_by("invoice_date")
    context = {"invoices": invoices}
    return render(request, "retail/invoices/list.html", context)