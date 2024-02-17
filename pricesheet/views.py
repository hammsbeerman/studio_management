from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from decimal import Decimal
from .forms import EnvelopeForm, CreateTemplateForm, NewTemplateForm, NCRForm
from .models import PriceSheet
from controls.models import SubCategory, FixedCost, SetPriceItem, SetPriceItemPrice
from controls.forms import SubCategoryForm, CategoryForm
from workorders.models import WorkorderItem, Category
from krueger.models import KruegerJobDetail, PaperStock
from inventory.models import Inventory
from krueger.forms import KruegerJobDetailForm
from workorders.forms import DesignItemForm

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
    print('modified')
    print(obj.edited)
    print(obj.category.pricesheet_type.id)
    item = get_object_or_404(PriceSheet, id=id)
    print(item.name)
    print(obj.category_id)
    #Get form to load from category
    loadform = Category.objects.get(id=obj.category_id)
    #formname = loadform.formname
    formname = globals()[loadform.formname]
    form = formname(instance=item)
    #form = NewTemplateForm(instance=obj)
    if not obj.edited:
        print('ned')
        fixed = FixedCost.objects.get(id=obj.category.pricesheet_type.id)
    else:
        print('ed')
        fixed = ''
    selected_paper = form.instance.paper_stock_id
    try:
        selected_paper = Inventory.objects.get(id=selected_paper)
        print(selected_paper.description)
        print(selected_paper)
    except: 
        selected_paper = ''
    papers = Inventory.objects.all()
    formdata = PriceSheet.objects.get(id=id)
    if request.method =="POST":
        print('posted')
        form = NewTemplateForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        print(id)
        edited = PriceSheet.objects.get(id=id)
        print(id)
        edited.edited = 1
        edited.save()
        context = {
            'message': 'Form saved successfully'
        }
        return redirect('pricesheet:template_list')
    context = {
        'template_id':id,
        'fixed':fixed,
        'form': form,
        'papers': papers,
        'selected_paper': selected_paper,
        'formdata': formdata,
    }
    return render(request, "pricesheet/templates/newtemplate_form.html", context)




def add_template(request):
    form = CreateTemplateForm()
    categories = Category.objects.all()
    if request.method =="POST":
        category = request.POST.get('category')
        subcategory = request.POST.get('subcategory')
        name = request.POST.get('name')
        print(category)
        form = CreateTemplateForm(request.POST)
        if form.is_valid():
            form.description = name
            form.save()
        else:
            print(form.errors)
        print(subcategory)
        #update template field
        try:
            template = SubCategory.objects.get(id=subcategory)
            template.template = 1
            template.save()
        except:
            template = Category.objects.get(id=category)
            template.template = 1
            template.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'teListChanged'})
       # else:
       #     print(form.errors)
    context = {
        'form': form,
        'categories': categories
    }
    return render (request, "pricesheet/modals/add_template.html", context)

def copy_template(request):
    if request.method == "POST":
        catid = request.POST.get('category')
        subcat = request.POST.get('subcategory')
        template = request.POST.get('template')
        name = request.POST.get('name')
        description = request.POST.get('description')
        print(name)
        print(description)
        obj = PriceSheet.objects.get(pk=template)
        obj.pk = None
        obj.name = name
        obj.description = description
        obj.subcategory_id = subcat
        obj.edited = 0
        obj.save()
        obj = SubCategory.objects.get(pk=subcat)
        obj.template = 1
        obj.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'TemplateListChanged'})
    catid = request.GET.get('category')
    template = request.GET.get('template')
    subcategory = SubCategory.objects.filter(category_id=catid).exclude(template=1)
    context = {
        'catid':catid,
        'template':template,
        'subcategory':subcategory
    }
    return render (request, "pricesheet/modals/copy_template.html", context)

def template_list(request, id=None):
    catid = id
    print(catid)
    if not catid:
        catid = request.GET.get('category')
    print(catid)
    category = Category.objects.all()
    subcategory = SubCategory.objects.filter(category_id=catid)
    template = PriceSheet.objects.filter(category_id=catid)
    #template = PriceSheet.objects.all().order_by('-category', '-name')
    context = {
        'template': template,
        'category': category,
        'subcategory':subcategory,
        'catid': catid,
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

def setprices(request):
    item = request.GET.get('setprice_category')
    print(item)
    obj = SetPriceItemPrice.objects.filter(name=item)
    try:
        selected = SetPriceItemPrice.objects.get(name=item)
    except:
        selected = ''
        pass
    print(item)
    print(obj)
    context = {
        'obj':obj,
        'selected':selected
    }
    return render(request, 'workorders/modals/setprices.html', context) 

def setqty(request):
    item = request.GET.get('setprice_item')
    print(item)
    obj = SetPriceItemPrice.objects.get(pk=item)
    print(item)
    print(obj)
    print(obj.description)
    context = {
        'obj':obj
    }
    return render(request, 'workorders/modals/setqty.html', context) 


def edititem(request, id, pk, cat,):
    if request.method == "POST":
        workorderitem = KruegerJobDetail.objects.get(workorder_item=pk)
        obj = get_object_or_404(KruegerJobDetail, pk=workorderitem.id)
        form = KruegerJobDetailForm(request.POST, instance=obj)
        workorder = request.POST.get('workorder')
        price_ea = request.POST.get('price_ea')
        internal_company = request.POST.get('internal_company')
        edited = 1
        if form.is_valid():
            obj = form.save(commit=False)
            obj.workorder.id = workorder
            obj.edited = edited
            obj.save()
            #update workorderitem table
            lineitem = WorkorderItem.objects.get(id=pk)
            lineitem.internal_company = internal_company
            lineitem.pricesheet_modified = edited
            lineitem.description = obj.description
            lineitem.quantity = obj.set_per_book
            lineitem.unit_price = price_ea
            lineitem.total_price = obj.price_total
            #lineitem.unit_price = 
            #lineitem.total_price = obj.price_total
            lineitem.save() 
        else:
            print(form.errors)
        return redirect('workorders:overview', id=obj.hr_workorder)
    if request.htmx:
        print('HTMX')
        
        modified = WorkorderItem.objects.get(pk=pk)

        internal_company = modified.internal_company
        #If new lineitem, load default pricing template
        if not modified.pricesheet_modified:
            #If there is a subcategory, load the pricing template for subcategory
            if modified.item_subcategory:
                description = WorkorderItem.objects.get(pk=pk)
                description = description.description
                item = get_object_or_404(PriceSheet, subcategory=modified.item_subcategory)
                formdata = PriceSheet.objects.get(subcategory_id = modified.item_subcategory)
            #Otherwise load category template
            else:
                print('cat')
                print(cat)
                item = get_object_or_404(PriceSheet, category=cat) 
                formdata = PriceSheet.objects.get(category_id = cat)
                description = ''
        #If item contains custom pricing load that               
        else:
            item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
            #formdata loads static data to template
            formdata = KruegerJobDetail.objects.get(workorder_item=pk)
            print('pk')
            print(pk)
            description = item.description
        #Get form to load from category
        loadform = Category.objects.get(id=cat)
        #formname = loadform.formname
        formname = globals()[loadform.formname]
        form = formname(instance=item)
        # if cat == 6:
        #     form = testform(instance=item)
        # if cat == 10:
        #     form = NCRForm(instance=item)
        #If paper is selected, load that
        selected_paper = form.instance.paper_stock_id
        print(selected_paper)
        try:
            selected_paper = Inventory.objects.get(id=selected_paper)
            print(selected_paper.description)
            print(selected_paper)
        except: 
            selected_paper = ''
        #populate paper list
        print('inventory cat')
        if loadform.inventory_category is not None:
            inventory_cat = loadform.inventory_category.id
            print(inventory_cat)
            papers = Inventory.objects.filter(inventory_category = inventory_cat)
        else:
            papers = Inventory.objects.all()
        context = {
            'form':form,
            'formdata':formdata,
            'description':description,
            'papers':papers,
            'selected_paper':selected_paper,
            'workorder_id':id,
            'internal_company':internal_company,

        }
        return render (request, "pricesheet/modals/edit_item.html", context)
    else:
        print('Not HTMX')
        print(pk)
        modified = WorkorderItem.objects.get(pk=pk)
        print('here')
        internal_company = modified.internal_company
        #If new lineitem, load default pricing template
        if not modified.pricesheet_modified:
            print('here')
            #If there is a subcategory, load the pricing template for subcategory
            if modified.item_subcategory:
                description = WorkorderItem.objects.get(pk=pk)
                description = description.description
                print('here')
                print(description)
                item = get_object_or_404(PriceSheet, subcategory=modified.item_subcategory)
                print('here')
                formdata = PriceSheet.objects.get(subcategory_id = modified.item_subcategory)
            #Otherwise load category template
            else:
                item = get_object_or_404(PriceSheet, category=cat)
                formdata = PriceSheet.objects.get(category_id = cat)
        #If item contains custom pricing load that               
        else:
            print('not here')
            item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
            #formdata loads static data to template
            formdata = KruegerJobDetail.objects.get(workorder_item=pk)
            print('pk')
            print(pk)
            print(formdata.internal_company)
            description = item.description
        #Get form to load from category
        loadform = Category.objects.get(id=cat)
        #formname = loadform.formname
        formname = globals()[loadform.formname]
        form = formname(instance=item)
        # if cat == 6:
        #     form = testform(instance=item)
        # if cat == 10:
        #     form = NCRForm(instance=item)
        #If paper is selected, load that
        selected_paper = form.instance.paper_stock_id
        print(selected_paper)
        try:
            selected_paper = Inventory.objects.get(id=selected_paper)
            print(selected_paper.description)
            print(selected_paper)
        except: 
            selected_paper = ''
        #populate paper list
        print('inventory cat')
        if loadform.inventory_category is not None:
            inventory_cat = loadform.inventory_category.id
            papers = Inventory.objects.filter(inventory_category = inventory_cat)
        else:
            papers = Inventory.objects.all()
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


@ require_POST
def remove_template(request):
    template = request.POST.get('template_id')
    category = request.POST.get('category_id')
    print(template)
    item = get_object_or_404(PriceSheet, pk=template)
    item.delete()
    return redirect('pricesheet:template_listing', id=category)





# @ require_POST
# def remove_workorder_item(request, pk):
#     item = get_object_or_404(WorkorderItem, pk=pk)
#     item.delete()
#     return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    

    














# # ####Working edititem
# def edititem(request, id, pk, cat,):
#     if request.method == "POST":
#         workorderitem = KruegerJobDetail.objects.get(workorder_item=pk)
#         obj = get_object_or_404(KruegerJobDetail, pk=workorderitem.id)
#         form = KruegerJobDetailForm(request.POST, instance=obj)
#         workorder = request.POST.get('workorder')
#         edited = 1
#         if form.is_valid():
#             obj = form.save(commit=False)
#             obj.workorder_id = workorder
#             obj.edited = edited
#             obj.save()
#             #update workorderitem table
#             lineitem = WorkorderItem.objects.get(id=pk)
#             lineitem.pricesheet_modified = edited
#             lineitem.description = obj.description
#             lineitem.quantity = obj.set_per_book
#             #lineitem.unit_price = 
#             #lineitem.total_price = obj.price_total
#             lineitem.save() 
#         else:
#             print(form.errors)
#         return redirect('workorders:overview', id=obj.hr_workorder)
#     if request.htmx:
#         print('HTMX')
#         print(pk)
#         item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
#         if cat == 6:
#             form = EnvelopeForm(instance=item)
#         if cat == 10:
#             form = NCRForm(instance=item)
#         if cat == 4:
#             form = testform(instance=item)
#         context = {
#             'form':form
#     }
#         return render (request, "pricesheet/modals/edit_item.html", context)
#     else:
#         print('Not HTMX')
#         modified = WorkorderItem.objects.get(pk=pk)
#         internal_company = modified.internal_company
#         #If new lineitem, load default pricing template
#         if not modified.pricesheet_modified:
#             #If there is a subcategory, load the pricing template for subcategory
#             if modified.item_subcategory:
#                 description = WorkorderItem.objects.get(pk=pk)
#                 description = description.description
#                 item = get_object_or_404(PriceSheet, subcategory=modified.item_subcategory)
#                 formdata = ''
#             #Otherwise load category template
#             else:
#                 item = get_object_or_404(PriceSheet, category=cat) 
#         #If item contains custom pricing load that               
#         else:
#             item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
#             #formdata loads static data to template
#             formdata = KruegerJobDetail.objects.get(workorder_item=pk)
#             print('pk')
#             print(pk)
#             description = item.description
#         if cat == 6:
#             form = EnvelopeForm(instance=item)
#         if cat == 10:
#             form = NCRForm(instance=item)
#         #If paper is selected, load that
#         selected_paper = form.instance.paper_stock_id
#         print(selected_paper)
#         try:
#             selected_paper = PaperStock.objects.get(id=selected_paper)
#             print(selected_paper.description)
#             print(selected_paper)
#         except: 
#             selected_paper = ''
#         #populate paper list
#         papers = PaperStock.objects.all()
#         context = {
#             'form':form,
#             'formdata':formdata,
#             'description':description,
#             'papers':papers,
#             'selected_paper':selected_paper,
#             'workorder_id':id,
#             'internal_company':internal_company,

#     }
#         return render(request, 'pricesheet/templates/master.html', context)


