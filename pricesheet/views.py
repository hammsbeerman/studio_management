from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from .forms import EnvelopeForm, SubCategoryForm, CategoryForm, CreateTemplateForm, NCRForm
from .models import PriceSheet, SubCategory
from workorders.models import WorkorderItem, Category
from krueger.models import KruegerJobDetail, PaperStock
from krueger.forms import KruegerJobDetailForm

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

def edititem(request, id, pk, cat,):
    if request.method == "POST":
        workorderitem = KruegerJobDetail.objects.get(workorder_item=pk)
        obj = get_object_or_404(KruegerJobDetail, pk=workorderitem.id)
        form = KruegerJobDetailForm(request.POST, instance=obj)
        workorder = request.POST.get('workorder')
        edited = 1
        if form.is_valid():
            obj = form.save(commit=False)
            obj.workorder = workorder
            obj.edited = edited
            obj.save()
            #update workorderitem table
            lineitem = WorkorderItem.objects.get(id=pk)
            lineitem.pricesheet_modified = edited
            lineitem.description = obj.description
            lineitem.quantity = obj.set_per_book
            #lineitem.unit_price = 
            #lineitem.total_price = obj.price_total
            lineitem.save() 
        else:
            print(form.errors)
        return redirect('workorders:overview', id=obj.hr_workorder)
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
        modified = WorkorderItem.objects.get(pk=pk)
        internal_company = modified.internal_company
        #If new lineitem, load default pricing template
        if not modified.pricesheet_modified:
            #If there is a subcategory, load the pricing template for subcategory
            if modified.item_subcategory:
                description = WorkorderItem.objects.get(pk=pk)
                description = description.description
                item = get_object_or_404(PriceSheet, subcategory=modified.item_subcategory)
                formdata = ''
            #Otherwise load category template
            else:
                item = get_object_or_404(PriceSheet, category=cat) 
        #If item contains custom pricing load that               
        else:
            item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
            #formdata loads static data to template
            formdata = KruegerJobDetail.objects.get(workorder_item=pk)
            print('pk')
            print(pk)
            description = item.description
        if cat == 6:
            form = EnvelopeForm(instance=item)
        if cat == 10:
            form = NCRForm(instance=item)
        #If paper is selected, load that
        selected_paper = form.instance.paper_stock_id
        print(selected_paper)
        try:
            selected_paper = PaperStock.objects.get(id=selected_paper)
            print(selected_paper.description)
            print(selected_paper)
        except: 
            selected_paper = ''
        #populate paper list
        papers = PaperStock.objects.all()
        context = {
            'form':form,
            'formdata':formdata,
            'description':description,
            'papers':papers,
            'selected_paper':selected_paper,
            'workorder_id':id,
            'internal_company':internal_company,

    }
        return render(request, 'pricesheet/templates/master.html', context)
