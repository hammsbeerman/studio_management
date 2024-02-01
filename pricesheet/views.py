from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from .forms import EnvelopeForm, SubCategoryForm, CategoryForm, CreateTemplateForm, NCRForm
from .models import PriceSheet, SubCategory
from workorders.models import WorkorderItem, Category
from krueger.models import KruegerJobDetail, PaperStock

def envelope(request, pk, cat):
    print(pk)
    item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
    #print(item.)
    #jobitem = get_object_or_404(KruegerJobDetail, workorder_item=item)
    print(item.id)
    print(item.edited)
    edited = item.edited
    if edited is True:
        form = EnvelopeForm(request.POST, instance=item)
        print("true")
    else:
        form = EnvelopeForm()
        print('false')
    category = cat
    print(item.description)
    if request.method == "POST":
        print('hello')
        category = request.POST.get('cat')
        form = EnvelopeForm(request.POST, instance=item)
        #form.instance.item_category = category
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
        else:
            print(form.errors)
    print(category)
    obj = Category.objects.get(id=category)        
    print(obj.name)
    form = EnvelopeForm(instance=item)
    context = {
        'form': form,
        'item': item,
        'obj': obj,
        'cat': category,
    }
    return render(request, 'pricesheet/modals/envelopes.html', context)

def template(request, id=None):
    obj = PriceSheet.objects.get(id=id)
    item = get_object_or_404(PriceSheet, id=id)
    print(item.name)
    form = EnvelopeForm(instance=obj)
    selected_paper = form.instance.paper_stock_id
    try:
        selected_paper = PaperStock.objects.get(id=selected_paper)
        print(selected_paper.description)
        print(selected_paper)
    except: 
        selected_paper = ''
    papers = PaperStock.objects.all()
    formdata = PriceSheet.objects.get(id=id)
    if request.method =="POST":
        form = EnvelopeForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            context = {
                'message': 'Form saved successfully'
            }
            return redirect('pricesheet:template_list')
    context = {
        'form': form,
        'papers': papers,
        'selected_paper': selected_paper,
        'formdata': formdata,
    }
    return render(request, "pricesheet/templates/envelope.html", context)


def add_category(request):
    form = CategoryForm()
    if request.method =="POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
        else:
            print(form.errors)
    context = {
        'form': form,
    }
    return render (request, "pricesheet/modals/add_category.html", context)

def add_subcategory(request):
    form = SubCategoryForm()
    if request.method =="POST":
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
        else:
            print(form.errors)
    context = {
        'form': form,
    }
    return render (request, "pricesheet/modals/add_subcategory.html", context)

def add_template(request):
    form = CreateTemplateForm()
    categories = Category.objects.all()
    if request.method =="POST":
        testing = request.POST.get('category')
        subcategory = request.POST.get('subcategory')
        print(testing)
        form = CreateTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            print(subcategory)
            #update template field
            template = SubCategory.objects.get(id=subcategory)
            template.template = 1
            template.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
        else:
            print(form.errors)
    context = {
        'form': form,
        'categories': categories
    }
    return render (request, "pricesheet/modals/add_template.html", context)



# def testtemplate(request, id, pk):
#     workorder = id
#     item = pk
#     print(workorder)
#     print(item)
#     obj = WorkorderItem.objects.get(id=item)
#     description = obj.description
#     jobitem = KruegerJobDetail.objects.get(workorder_item=item)
#     #print(jobitem.workorder_id)
#     jobobj = jobitem.id
#     jobid = jobobj
#     obj = get_object_or_404(KruegerJobDetail, id=jobobj)
#     form = KruegerJobDetailForm(instance=obj)
#     #print(obj.__dict__)
#     internal_company = form.instance.internal_company
#     selected_paper = form.instance.paper_stock_id
#     try:
#         selected_paper = PaperStock.objects.get(id=selected_paper)
#         print(selected_paper.description)
#         print(selected_paper)
#     except: 
#         selected_paper = ''
#     formdata = KruegerJobDetail.objects.get(id=jobid)
#     print(formdata)
#     #selected_paper = formdata.paper_stock.description
#     papers = PaperStock.objects.all()
#     #print(form.instance.internal_company)
#     obj = Workorder.objects.get(workorder=workorder)
#     print('workorder')
#     print(obj.id)
#     workorder_id = obj.id
#     #print(form.instance.paper_stock_id)
#     #print(form.instance.paper_stock_id)
#     #print(formdata.paper_stock_id)
#     #print(selected_paper)
#     if request.method == "POST":
#         # print('poster')
#         jobid = request.POST.get('jobid')
#         workorderid = request.POST.get('workorder')
#         obj = get_object_or_404(KruegerJobDetail, pk=jobid)
#         form = KruegerJobDetailForm(request.POST, instance=obj)
#         #print(form.cleaned_data)
#         papers = PaperStock.objects.all()
#         obj = Workorder.objects.get(workorder=workorder)
#         workorder = obj.workorder
#         print('workorder')
#         # print(obj.workorder)
#         print(workorderid)
#         #print(obj.__dict__)
#         print('endworkorder')
#         form.instance.workorder_item = item
#         #form.instance.workorder_id = workorderid
#         form.instance.hr_workorder = obj.workorder
#         form.instance.company = obj.internal_company
#         form.instance.customer_id = obj.customer_id
#         form.instance.hr_customer = obj.hr_customer
#         if form.is_valid():
#             lineitem = WorkorderItem.objects.get(id=item)
#             lineitem.description = form.instance.description
#             print(lineitem.description)
#             lineitem.save()
#             form.save()
#             print(form.errors)
#             messages.success(request, 'Successfully Saved')
#             return redirect('workorders:overview', id=obj.workorder)
#         else:
#             print(form.errors)
#     context = {
#         "form": form,
#         "description": description,
#         "title": "New Job",
#         'jobid':jobid,
#         'papers': papers,
#         'formdata':formdata,
#         'internal_company':internal_company,
#         'selected_paper':selected_paper,
#         'workorder_id': workorder_id
#         #'papersizes': papersizes,
#     }
#     return render(request, "krueger/pricingforms/bigform.html", context)

def template_list(request):
    template = PriceSheet.objects.all().order_by('-category', '-name')
    context = {
        'template': template,
    }
    return render(request, 'pricesheet/list.html', context)

def subcategory(request):
    cat = request.GET.get('category')
    print(cat)
    obj = SubCategory.objects.filter(category_id=cat).exclude(template=1)
    context = {
        'obj':obj
    }
    return render(request, 'pricesheet/modals/subcategory.html', context) 

def edititem(request, id, pk, cat):
    if request.htmx:
        print('HTMX')
        print(pk)
        item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
        if cat == 6:
            form = EnvelopeForm(instance=item)
        if cat == 10:
            form = NCRForm(instance=item)
        context = {
            'form':form
    }
        return render (request, "pricesheet/modals/edit_item.html", context)
    else:
        print('Not HTMX')
        print(pk)
        item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
        if cat == 6:
            form = EnvelopeForm(instance=item)
        if cat == 10:
            form = NCRForm(instance=item)
        context = {
            'form':form
    }
    return render(request, 'pricesheet/templates/master.html', context)