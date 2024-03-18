from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from accounts.decorators import allowed_users
from decimal import Decimal
from .forms import EnvelopeForm, CreateTemplateForm, NewTemplateForm, NCRForm, CreateWideFormatTemplateForm, WideFormatForm
from .models import PriceSheet, WideFormatPriceSheet
from controls.models import SubCategory, FixedCost, SetPriceItem, SetPriceItemPrice
from controls.forms import SubCategoryForm, CategoryForm
from workorders.models import WorkorderItem, Category
from krueger.models import KruegerJobDetail, PaperStock, WideFormat
from inventory.models import Inventory
from krueger.forms import KruegerJobDetailForm, WideFormatDetailForm
from workorders.forms import DesignItemForm

@login_required
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

@login_required
def template(request, id=None):
    obj = PriceSheet.objects.get(id=id)
    print('modified')
    print(obj.edited)
    print(obj.category.pricesheet_type.id)
    #print(obj.subcategory.inventory_category.id)
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
    test = Inventory.objects.filter(inventory_category = 4)
    print(test)
    try:
        papers = Inventory.objects.filter(inventory_category = obj.subcategory.inventory_category.id).order_by('name')
        #papers = Inventory.objecs.get(inventory_category=obj.subcategory.inventory_category.id)
        print(papers)
        print(1)
    except:
        papers = Inventory.objects.all().order_by('name')
        print(2)
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

@login_required
def add_template(request):
    form = CreateTemplateForm()
    categories = Category.objects.all().exclude(active=0).distinct().order_by('name')
    if request.method =="POST":
        category = request.POST.get('category')
        subcategory = request.POST.get('subcategory')
        name = request.POST.get('name')
        print(category)
        category_type = Category.objects.get(id=category)
        if category_type.wideformat == 1:
            form = CreateWideFormatTemplateForm(request.POST)
        else:
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

@login_required
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

@login_required
@allowed_users(allowed_roles=['admin'])
def template_list(request, id=None):
    catid = id
    print(catid)
    if not catid:
        catid = request.GET.get('category')
    print(catid)
    category = Category.objects.all().exclude(active=0).distinct().order_by('name')
    subcategory = SubCategory.objects.filter(category_id=catid)
    template = PriceSheet.objects.filter(category_id=catid)
    wftemplate = WideFormatPriceSheet.objects.filter(category_id=catid)
    #template = PriceSheet.objects.all().order_by('-category', '-name')
    context = {
        'template': template,
        'wftemplate': wftemplate,
        'category': category,
        'subcategory':subcategory,
        'catid': catid,
    }
    return render(request, 'pricesheet/list.html', context)

@login_required
def subcategory(request):
    cat = request.GET.get('category')
    print(cat)
    obj = SubCategory.objects.filter(category_id=cat).exclude(template=1)
    context = {
        'obj':obj
    }
    return render(request, 'pricesheet/modals/subcategory.html', context) 

@login_required
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

@login_required
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


@login_required
def edititem(request, id, pk, cat,):
    if request.method == "POST":
        workorderitem = KruegerJobDetail.objects.get(workorder_item=pk)
        obj = get_object_or_404(KruegerJobDetail, pk=workorderitem.id)
        form = KruegerJobDetailForm(request.POST, instance=obj)
        workorder = request.POST.get('workorder')
        price_ea = request.POST.get('price_ea')
        paperstock = request.POST.get('paper_stock')
        print('pk')
        print(pk)
        try:
            print(paperstock)
            KruegerJobDetail.objects.filter(workorder_item=pk).update(paper_stock_id = paperstock, billed=1)
            print('up')
        except:
            test = KruegerJobDetail.objects.filter(workorder_item=pk)
            print('test')
            print(test)
        print(paperstock)
        internal_company = request.POST.get('internal_company')
        edited = 1
        if form.is_valid():
            obj = form.save(commit=False)
            obj.workorder.id = workorder
            obj.edited = edited
            total = obj.price_total
            override = obj.override_price
            if override:
                print(type(override))
                override = (float(override))
                temp_total = override
                #print(type(obj.quantity))
                price_ea = temp_total / obj.set_per_book
            else:
                temp_total = total
            obj.save()
            #print(pk)
            #KruegerJobDetail.objects.filter(pk=pk).update(paper_stock_id = paperstock)
            #update workorderitem table
            lineitem = KruegerJobDetail.objects.get(workorder_item=pk)
            lineitem.paper_stock_id = paperstock
            lineitem.save()
            lineitem = WorkorderItem.objects.get(id=pk)
            lineitem.internal_company = internal_company
            lineitem.pricesheet_modified = edited
            lineitem.description = obj.description
            lineitem.quantity = obj.set_per_book
            lineitem.unit_price = price_ea
            lineitem.total_price = obj.price_total
            lineitem.override_price = override
            lineitem.pricesheet_modified = 1
            lineitem.absolute_price = temp_total
            tax_percent = .055
            tax = 1.055
            lineitem.absolute_price = (float(lineitem.absolute_price))
            if lineitem.tax_exempt == 1:
                lineitem.tax_amount = 0
                lineitem.total_with_tax = lineitem.absolute_price
            else:
                print('absolute price')
                print(type(lineitem.absolute_price))
                lineitem.tax_amount = lineitem.absolute_price * tax_percent
                lineitem.total_with_tax = lineitem.absolute_price * tax
            if lineitem.notes:
                notes = lineitem.notes
            else:
                notes = ''
            if lineitem.last_item_order:
                last_order = lineitem.last_item_order
            else:
                last_order = ''
            if lineitem.last_item_price:
                last_price = lineitem.last_item_order
            else:
                last_price = ''
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
            papers = Inventory.objects.filter(inventory_category = inventory_cat).order_by('name')
        else:
                try:
                    papers = Inventory.objects.filter(inventory_category = modified.item_subcategory.inventory_category.id).order_by('name')
                    #papers = Inventory.objecs.get(inventory_category=obj.subcategory.inventory_category.id)
                    print(papers)
                    print(1)
                except:
                    papers = Inventory.objects.all().order_by('name')
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
                details = WorkorderItem.objects.get(pk=pk)
                description = details.description
                print('here')
                print(description)
                item = get_object_or_404(PriceSheet, subcategory=modified.item_subcategory)
                print('here')
                formdata = PriceSheet.objects.get(subcategory_id = modified.item_subcategory)
                formdata.description = description
                formdata.internal_company = details.internal_company
            #Otherwise load category template
            else:
                item = get_object_or_404(PriceSheet, category=cat)
                formdata = PriceSheet.objects.get(category_id = cat)
        #If item contains custom pricing load that               
        else:
            print('not here')
            item = get_object_or_404(KruegerJobDetail, workorder_item=pk)
            #formdata loads static data to template
            print()
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
            #papers = Inventory.objects.filter(inventory_category = inventory_cat)
        try:
            papers = Inventory.objects.filter(inventory_category = modified.item_subcategory.inventory_category.id).order_by('name')
            #papers = Inventory.objecs.get(inventory_category=obj.subcategory.inventory_category.id)
            print(papers)
            print('1')
        except:
            try:
                papers = Inventory.objects.filter(inventory_category = inventory_cat).order_by('name')
            except:
                papers = Inventory.objects.all().order_by('name')
                print('2')
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
@login_required
def remove_template(request):
    template = request.POST.get('template_id')
    category = request.POST.get('category_id')
    print(template)
    item = get_object_or_404(PriceSheet, pk=template)
    item.delete()
    return redirect('pricesheet:template_listing', id=category)




@login_required
def edit_wideformat_item(request, pk, cat,):
    if request.method == "POST":
        workorderitem = WideFormat.objects.get(workorder_item=pk)
        obj = get_object_or_404(WideFormat, pk=workorderitem.id)
        form = WideFormatForm(request.POST, instance=obj)
        workorder = request.POST.get('workorder')
        price_ea = request.POST.get('price_ea')
        internal_company = request.POST.get('internal_company')
        material = request.POST.get('paper_stock')
        mask = request.POST.get('mask')
        laminate = request.POST.get('laminate')
        substrate = request.POST.get('substrate')
        edited = 1
        if form.is_valid():
            #print(request.POST)
            obj = form.save(commit=False)
            obj.workorder.id = workorder
            obj.edited = edited
            obj.material_id = material
            total = obj.price_total
            override = obj.override_price
            if override:
                print(type(override))
                override = (float(override))
                temp_total = override
                print(type(obj.quantity))
                price_ea = temp_total / obj.quantity
            else:
                temp_total = total
            if mask.isnumeric():
                obj.mask_id = mask
            if laminate.isnumeric():
                obj.laminate_id = laminate
            if substrate.isnumeric():
                obj.substrate_id = substrate
            obj.save()
            #update workorderitem table
            print('temptotal')
            print(temp_total)
            lineitem = WorkorderItem.objects.get(id=pk)
            lineitem.internal_company = internal_company
            lineitem.description = obj.description
            lineitem.quantity = obj.quantity
            lineitem.unit_price = price_ea
            lineitem.total_price = obj.price_total
            lineitem.override_price = override
            lineitem.pricesheet_modified = 1
            lineitem.absolute_price = temp_total
            tax_percent = Decimal.from_float(.055)
            tax = Decimal.from_float(1.055)
            if lineitem.tax_exempt == 1:
                lineitem.tax_amount = 0
                lineitem.total_with_tax = lineitem.absolute_price
            else:
                # print(type(tax_percent))
                # print(tax_percent)
                # print(type(lineitem.absolute_price))
                # print(lineitem.absolute_price)
                #tax_percent = (float(tax_percent))
                #print(tax_percent)
                absolute_price = (float(lineitem.absolute_price))
                #print(type(absolute_price))
                absolute_price = Decimal.from_float(absolute_price)
                #print(type(absolute_price))
                #print(absolute_price)
                lineitem.tax_amount = absolute_price * tax_percent
                print('tax_amount')
                print(lineitem.tax_amount)
                lineitem.total_with_tax = absolute_price * tax
            if lineitem.notes:
                notes = lineitem.notes
            else:
                notes = ''
            if lineitem.last_item_order:
                last_order = lineitem.last_item_order
            else:
                last_order = ''
            if lineitem.last_item_price:
                last_price = lineitem.last_item_order
            else:
                last_price = ''
            lineitem.save() 
        else:
            print(form.errors)
        return redirect('workorders:overview', id=obj.hr_workorder)
    if request.htmx:
        print('HTMX')
        
        # modified = WorkorderItem.objects.get(pk=pk)

        # internal_company = modified.internal_company
        # #If new lineitem, load default pricing template
        # if not modified.pricesheet_modified:
        #     #If there is a subcategory, load the pricing template for subcategory
        #     if modified.item_subcategory:
        #         description = WorkorderItem.objects.get(pk=pk)
        #         description = description.description
        #         item = get_object_or_404(PriceSheet, subcategory=modified.item_subcategory)
        #         formdata = PriceSheet.objects.get(subcategory_id = modified.item_subcategory)
        #     #Otherwise load category template
        #     else:
        #         print('cat')
        #         print(cat)
        #         item = get_object_or_404(PriceSheet, category=cat) 
        #         formdata = PriceSheet.objects.get(category_id = cat)
        #         description = ''
        # #If item contains custom pricing load that               
        # else:
        #     item = get_object_or_404(WideFormat, workorder_item=pk)
        #     #formdata loads static data to template
        #     formdata = WideFormat.objects.get(workorder_item=pk)
        #     print('pk')
        #     print(pk)
        #     description = item.description
        # #Get form to load from category
        # loadform = Category.objects.get(id=cat)
        # #formname = loadform.formname
        # formname = globals()[loadform.formname]
        # form = formname(instance=item)
        # # if cat == 6:
        # #     form = testform(instance=item)
        # # if cat == 10:
        # #     form = NCRForm(instance=item)
        # #If paper is selected, load that
        # selected_paper = form.instance.paper_stock_id
        # print(selected_paper)
        # try:
        #     selected_paper = Inventory.objects.get(id=selected_paper)
        #     print(selected_paper.description)
        #     print(selected_paper)
        # except: 
        #     selected_paper = ''
        # #populate paper list
        # print('inventory cat')
        # if loadform.inventory_category is not None:
        #     inventory_cat = loadform.inventory_category.id
        #     print(inventory_cat)
        #     papers = Inventory.objects.filter(inventory_category = inventory_cat)
        # else:
        #     papers = Inventory.objects.all()
        # context = {
        #     'form':form,
        #     'formdata':formdata,
        #     'description':description,
        #     'papers':papers,
        #     'selected_paper':selected_paper,
        #     'workorder_id':id,
        #     'internal_company':internal_company,

        # }
        # return render (request, "pricesheet/modals/edit_item.html", context)
    else:
        print('Not HTMX')
        print(pk)
        modified = WorkorderItem.objects.get(pk=pk)
        print('here')
        internal_company = modified.internal_company
        #If new lineitem, load default pricing template
        if not modified.pricesheet_modified:
            print('here1')
            #If there is a subcategory, load the pricing template for subcategory
            if modified.item_subcategory:
                details = WorkorderItem.objects.get(pk=pk)
                description = details.description
                print('here2')
                print(description)
                item = get_object_or_404(WideFormatPriceSheet, subcategory=modified.item_subcategory)
                print('here3')
                formdata = WideFormatPriceSheet.objects.get(subcategory_id = modified.item_subcategory)
                #('desc')
                #print(formdata.description)
                formdata.description = description
                formdata.internal_company = details.internal_company
            #Otherwise load category template
            else:
                item = get_object_or_404(WideFormatPriceSheet, category=cat)
                formdata = WideFormatPriceSheet.objects.get(category_id = cat)
        #If item contains custom pricing load that               
        else:
            print('not here')
            item = get_object_or_404(WideFormat, workorder_item=pk)
            #formdata loads static data to template
            formdata = WideFormat.objects.get(workorder_item=pk)
            print(formdata.description)
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
        print(formname)
        selected_paper = form.instance.material_id
        print(selected_paper)
        try:
            selected_paper = Inventory.objects.get(id=selected_paper)
            print(selected_paper.description)
            print(selected_paper)
        except: 
            selected_paper = ''
        mask = form.instance.mask_id
        try:
            mask = Inventory.objects.get(id=mask)
        except: 
            mask = ''
        print('mask')
        print(mask)
        laminate = form.instance.laminate_id
        try:
            laminate = Inventory.objects.get(id=laminate)
        except: 
            laminate = ''
        substrate = form.instance.substrate_id
        try:
            substrate = Inventory.objects.get(id=substrate)
        except: 
            substrate = ''
        #populate paper list
        print('inventory cat')
        if loadform.inventory_category is not None:
            inventory_cat = loadform.inventory_category.id
            papers = Inventory.objects.filter(type_vinyl = 1).order_by('name')
            masks = Inventory.objects.filter(type_mask = 1).order_by('name')
            laminates = Inventory.objects.filter(type_laminate = 1).order_by('name')
            substrates = Inventory.objects.filter(type_substrate = 1).order_by('name')
        else:
            papers = Inventory.objects.all().order_by('name')
        context = {
            'form':form,
            'formdata':formdata,
            'description':description,
            'papers':papers,
            'selected_paper':selected_paper,
            'mask':mask,
            'masks':masks,
            'laminate':laminate,
            'laminates':laminates,
            'substrate':substrate,
            'substrates':substrates,
            'workorder_id':id,
            'internal_company':internal_company,

        }
        return render(request, 'pricesheet/templates/wideformat.html', context)
    
@login_required
def wideformat_template(request, id=None):
    obj = WideFormatPriceSheet.objects.get(id=id)
    print('modified')
    print(obj.edited)
    print(obj.category.pricesheet_type.id)
    item = get_object_or_404(WideFormatPriceSheet, id=id)
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
        print(obj.category.pricesheet_type.id)
    else:
        print('ed')
        fixed = ''
    selected_paper = form.instance.material_id
    mask = form.instance.mask_id
    laminate = form.instance.laminate_id
    substrate = form.instance.substrate_id
    print('selected paper')
    print(selected_paper)
    try:
        selected_paper = Inventory.objects.get(id=selected_paper)
        print(selected_paper.description)
        print(selected_paper)
    except: 
        selected_paper = ''
    try: 
        mask = Inventory.objects.get(id=mask)
    except:
        mask = ''
    try: 
        laminate = Inventory.objects.get(id=laminate)
    except:
        laminate = ''
    try: 
        substrate = Inventory.objects.get(id=substrate)
    except:
        substrate = ''
    papers = Inventory.objects.all()
    masks = Inventory.objects.filter(type_mask = 1).order_by('name')
    laminates = Inventory.objects.filter(type_laminate = 1).order_by('name')
    substrates = Inventory.objects.filter(type_substrate = 1).order_by('name')
    formdata = WideFormatPriceSheet.objects.get(id=id)
    if request.method =="POST":
        mask = request.POST.get('mask')
        laminate = request.POST.get('laminate')
        substrate = request.POST.get('substrate')
        print(mask)
        print(laminate)
        print(substrate)
        print('posted')
        form = WideFormatForm(request.POST, instance=item)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                int(mask)
                obj.mask_id = mask
            except:
                pass
            try:
                int(laminate)
                obj.laminate_id = laminate
            except:
                pass
            try:
                int(substrate)
                obj.substrate_id = substrate
            except:
                pass
            obj.save()
        else:
            print(form.errors)
        print(id)
        edited = WideFormatPriceSheet.objects.get(id=id)
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
        'mask':mask,
        'masks':masks,
        'laminates':laminates,
        'laminate':laminate,
        'substrates':substrates,
        'substrate':substrate,
        'formdata': formdata,
    }
    return render(request, "pricesheet/templates/wideformat_template_form.html", context)