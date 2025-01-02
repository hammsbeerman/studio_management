from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from datetime import timedelta, datetime
from .models import StoreItemDetails, StoreItemDetailHistory
from inventory.models import InventoryMaster
from .forms import StoreItemDetailForm


@login_required
def online_store_main(request):
    return render (request, "onlinestore/dashboard.html")

@login_required
def store_items(request):
    items = StoreItemDetails.objects.all()
    for x in items:
        high_cost = x.high_cost
        current_price = x.online_store_price
        if high_cost:
            oneforty = high_cost * Decimal(str(1.4))
            print(high_cost)
            print(current_price)
            print(oneforty)
            try:
                actual = current_price / high_cost * 100
            except:
                actual = '0'
            StoreItemDetails.objects.filter(pk=x.pk).update(oneforty_percent=oneforty, actual_markup=actual)
    items = StoreItemDetails.objects.all()
    context = {
        'items':items,
    }
    return render (request, "onlinestore/store_items.html", context)

@login_required
def store_item_detail(request):
    item = request.GET.get('item')
    items = StoreItemDetails.objects.all()
    print(item)
    item = StoreItemDetails.objects.get(pk=item)
    high_cost = item.high_cost
    current_price = item.online_store_price
    if high_cost:
        oneforty = high_cost * Decimal(str(1.4))
        print(high_cost)
        print(current_price)
        print(oneforty)
        try:
            actual = current_price / high_cost
        except:
            actual = '0'
        StoreItemDetails.objects.filter(pk=item.pk).update(oneforty_percent=oneforty, actual_markup=actual)
    context = {
        'item':item,
        'items':items,
    }
    return render (request, "onlinestore/partials/store_items_detail.html", context)

@login_required
def edit_store_item(request, detail=None):
    if request.method == "POST":
        form = StoreItemDetailForm(request.POST)
        if form.is_valid():
            online = form.instance.online_store_price
            retail = form.instance.retail_store_price
            item = request.POST.get('item')
            item = int(item)
            detail = request.POST.get('detail')
            print(item)
            date = request.POST.get('date')
            date = datetime.strptime(date, '%m/%d/%Y')
            current_price = StoreItemDetails.objects.get(id=item)
            if not online:
                online = current_price.online_store_price
            if not retail:
                retail = current_price.retail_store_price
            print(date)
            print(online)
            print(retail)
            StoreItemDetails.objects.filter(pk=item).update(online_store_price=online, retail_store_price=retail, date_last_price_change=date)
            master = StoreItemDetails.objects.get(pk=item)
            masterpart = master.item.id
            print('master part number')
            print(masterpart)
            StoreItemDetailHistory.objects.create(item=InventoryMaster.objects.get(pk=masterpart), online_store_price=online, retail_store_price=retail, date_last_price_change=date)
            if detail:
                print("detail")
                print(detail)
                return redirect('finance:open_invoices_recieve_payment', item=item)
            print('hello')
            return HttpResponse(status=204, headers={'HX-Trigger': 'ItemPriceChanged'})
    item = request.GET.get('item')
    item = StoreItemDetails.objects.get(pk=item)
    form = StoreItemDetailForm
    context = {
        'item':item,
        'form':form,
    }
    return render (request, "onlinestore/modals/edit_store_item.html", context)