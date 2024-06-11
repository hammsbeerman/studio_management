from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from controls.models import RetailInventoryCategory, RetailInventorySubCategory


@login_required
def retail_home(request):
    cats = RetailInventoryCategory.objects.all()
    context = {
        'cats':cats
    }
    return render(request, "retail/main.html", context)

@login_required
def subcat(request, cat):
    #cat = 2
    cats = RetailInventorySubCategory.objects.filter(inventory_category=cat)
    context = {
        'cats':cats
    }
    return render(request, "retail/sub.html", context)

@login_required
def parent(request, cat=None):
    #cat = 2
    cats = RetailInventoryCategory.objects.filter(parent=cat)
    context = {
        'cats':cats
    }
    return render(request, "retail/parent.html", context)