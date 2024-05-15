from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from .forms import SubCategoryForm, CategoryForm, AddSetPriceItemForm, AddSetPriceCategoryForm
from .models import SetPriceCategory, SubCategory, Category, SetPriceItemPrice
from workorders.models import Workorder
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
    category = Category.objects.all().exclude(active=0).order_by('name')
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
                lineitem = SetPriceCategory(category=obj.category, name=obj.name)
                lineitem.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ListChanged'})
            else:
                form.save()
                return HttpResponse(status=204, headers={'HX-Trigger': 'ListChanged'})
        else:
            print(form.errors)
    context = {
        'categories':category,
        'form': form,
    }
    return render (request, "pricesheet/modals/add_subcategory.html", context)

@login_required
def add_setprice_category(request):
    form = AddSetPriceCategoryForm()
    category = 3
    updated = timezone.now()
    if request.method =="POST":
        form = AddSetPriceCategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated = updated
            obj.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'CategoryAdded'})
        else:
            print(form.errors)
    context = {
        'form': form,
        'category':category,
    }
    return render (request, "pricesheet/modals/add_setprice_category.html", context)


@login_required
def add_setprice_item(request):
    form = AddSetPriceItemForm()
    updated = timezone.now()
    if request.method =="POST":
        form = AddSetPriceItemForm(request.POST)
        cat = 3
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated = updated
            obj.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'TemplateListChanged', 'category':'3'})
        else:
            print(form.errors)
    context = {
        'form': form,
    }
    return render (request, "pricesheet/modals/add_setprice_item.html", context)

# @login_required
# def setprice_list(request):
#     subcat = request.GET.get('subcat')
#     items = SetPriceItemPrice.objects.filter(name_id = subcat)
#     print(items)
#     context = {
#         'items':items
#     }
#     return render (request, "pricesheet/partials/setprice_list.html", context)

@login_required
def utilities(request):
    return render (request, "controls/utilities.html")


@login_required
def mark_all_verified(request):
    workorder = Workorder.objects.filter(completed=1)
    for x in workorder:
        print(x.workorder)
        Workorder.objects.filter(pk=x.pk).update(checked_and_verified=1)
    return render (request, "controls/utilities.html")

@login_required
def mark_all_invoiced(request):
    workorder = Workorder.objects.filter(completed=1).exclude(billed=0)
    for x in workorder:
        print(x.workorder)
        Workorder.objects.filter(pk=x.pk).update(invoice_sent=1)
    return render (request, "controls/utilities.html")

@login_required
def missing_workorders(request):
    if request.method =="POST":
        start = request.POST.get('start')
        end = request.POST.get('end')
        company = request.POST.get('company')
        try:
            start = int(start)
        except:
            return render (request, "controls/missing_workorders.html")
        try:
            end = int(end)
        except:
            return render (request, "controls/missing_workorders.html")
        workorders = list(range(start, end + 1))
        print(workorders)
        # max = workorders[0]
        # for i in workorders:
        #     #print(i)
        #     if i > max:
        #         max = i
        # print(max)
        #test = 3
        # if company == test:
        #     print('same')
        print(company)
        company = int(company)
        if company == 1:
            print('printleader')
            #xisting = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('kos_workorder', flat=True)
            existing = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('printleader_workorder', flat=True)
        elif company == 2:
            print('lk')
            #xisting = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('kos_workorder', flat=True)
            existing = Workorder.objects.filter(lk_workorder__isnull=False).values_list('lk_workorder', flat=True)
        elif company == 3:
            print('kos')
            #xisting = Workorder.objects.filter(printleader_workorder__isnull=False).values_list('kos_workorder', flat=True)
            existing = Workorder.objects.filter(kos_workorder__isnull=False).values_list('printleader_workorder', flat=True)
        else:
            print('broken')
            return render (request, "controls/missing_workorders.html")
        exist = (list(existing))
        print(exist)
        try:
            cleaned = [eval(i) for i in exist]
        except:
            return render (request, "controls/missing_workorders.html")
        print(cleaned)

        set1 = set(workorders)
        set2 = set(cleaned)


        missing = list(sorted(set1 - set2))
        print('missing:', missing)
        context = {
            'missing':missing,
        }
        return render (request, "controls/missing_workorders.html", context)
    return render (request, "controls/missing_workorders.html")

@login_required
def update_complete_date(request):
    workorder = Workorder.objects.filter(completed=1)
    for x in workorder:
        print(x.workorder)
        date = x.updated
        print(date)
        Workorder.objects.filter(pk=x.pk).update(date_completed=date)
    return render (request, "controls/utilities.html")

def special_tools(request):
    return render (request, "controls/specialized_tools.html")
    




