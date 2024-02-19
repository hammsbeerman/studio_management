from django.shortcuts import render
from django.http import HttpResponse
from .forms import SubCategoryForm, CategoryForm
from .models import SetPriceItem, SubCategory
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
                lineitem = SetPriceItem(category=obj.category, name=obj.name)
                lineitem.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ListChanged'})
            else:
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ListChanged'})
        else:
            print(form.errors)
    context = {
        'form': form,
    }
    return render (request, "pricesheet/modals/add_subcategory.html", context)
