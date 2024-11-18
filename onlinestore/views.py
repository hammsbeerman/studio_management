from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import StoreItemDetails


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
                actual = current_price / high_cost
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