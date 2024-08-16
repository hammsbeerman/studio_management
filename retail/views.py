from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal
from controls.models import RetailInventoryCategory, RetailInventorySubCategory
from .forms import AddVendorForm, AddInvoiceForm, AddInvoiceItemForm, AddInvoiceItemRemainderForm, RetailVendorItemDetailForm, RetailInventoryMasterForm
from .models import RetailInvoices, RetailInvoiceItem, RetailVendorItemDetail, RetailInventoryMaster
from inventory.models import Vendor

####################Not being used
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

####################################





# def invoice_item_remainder(request, vendor=None, invoice=None):
#     # invoice = invoice
#     # vendor = vendor
#     item_id = request.GET.get('name')
#     if item_id:
#         try:
#             item = get_object_or_404(RetailInvoiceItem, internal_part_number=item_id, vendor=vendor)
#             form = AddInvoiceItemRemainderForm(instance=item)
#         except:
#             print('sorry')
#             item = ''
#             form = ''
#             vendor = ''
#         # print(item.description)
#         # print(item_id)
#         print(vendor)
#         form = AddInvoiceItemForm
#         context = {
#             'form':form,
#             'vendor':vendor,
#             'invoice':invoice,
#         }
#         return render (request, "retail/invoices/partials/invoice_item_remainder.html", context)
    


def vendor_item_remainder(request, vendor=None, invoice=None):
    form = RetailVendorItemDetailForm
    # invoice = invoice
    # vendor = vendor
    item_id = request.GET.get('item')
    print(item_id)
    if item_id:
        try:
            item = get_object_or_404(RetailInventoryMaster, pk=item_id)
            print(item.id)
            print('hello')
            name = item.name
            description = item.description
            ipn = item.id
        except:
            print('sorry')
            #item = ''
            #form = ''
            vendor = ''
        print(vendor)
        form = AddInvoiceItemForm
        context = {
            'form':form,
            'name':name,
            'description':description,
            'ipn':ipn,
            'vendor':vendor,
            'invoice':invoice,
        }
        return render (request, "retail/invoices/partials/vendor_item_remainder.html", context)


# def invoice_item_remainder(request, vendor=None, invoice=None):
#     item_id = request.GET.get('name')
#     if item_id:
#         try:
#             item = get_object_or_404(RetailInvoiceItem, internal_part_number=item_id, vendor=vendor)
#             form = AddInvoiceItemRemainderForm(instance=item)
#         except:
#             print('sorry')
#             item = ''
#             form = ''
#             vendor = ''
#         print(vendor)
#         form = AddInvoiceItemForm
#         context = {
#             'form':form,
#             'vendor':vendor,
#             'invoice':invoice,
#         }
#         return render (request, "retail/invoices/partials/invoice_item_remainder.html", context)







#####################################################################################################################################################


@login_required
def add_vendor(request):
    form = AddVendorForm()
    # if request.htmx:
    #     if request.method == "POST":
    #         form = AddVendorForm(request.POST)
    #         pk = request.POST.get('item')
    #         cat = request.POST.get('cat')
    #         if form.is_valid():
    #             form.save()
    #             context = {
    #                 'pk': pk,
    #                 'cat': cat,
    #             }
    #             return redirect('workorders:edit_orderout_item', pk=pk, cat=cat)
        # pk = request.GET.get('item')
        # cat = request.GET.get('cat')
        # print(pk)
        # print(cat)
        # context = {
        #         'form': form,
        #         'pk': pk,
        #         'cat': cat,
        #         #'categories': categories
        #     }
        # return render (request, "inventory/vendors/add_vendor_modal.html", context)
    if request.method == "POST":
        form = AddVendorForm(request.POST)
        if form.is_valid():
            form.save()
        vendors = Vendor.objects.filter(retail_vendor = 1).order_by("name")
        #print(vendor)
        context = {
            'vendors': vendors,
        }
        return render (request, "retail/vendors/list.html", context)
    context = {
        'form': form,
        #'categories': categories
    }
    return render (request, "retail/vendors/add_vendor.html", context)

@login_required
def vendor_list(request):
    vendor = Vendor.objects.filter(retail_vendor = 1).order_by("name")
    print('vendors')
    context = {
        'vendors': vendor,
    }
    return render(request, 'retail/vendors/list.html', context)

@login_required
def vendor_detail(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    context = {
        'vendor': vendor,
    }
    return render(request, 'retail/vendors/detail.html', context)

@login_required
def invoice_list(request):
    invoices = RetailInvoices.objects.all().order_by("invoice_date")
    print('invoice')
    context = {
        'invoices': invoices,
    }
    return render(request, 'retail/invoices/list.html', context)

# @login_required
# def invoice_detail(request, id=None):
#     if request.method == "POST":
#         invoice = request.POST.get('invoice')
#         vendor = request.POST.get('vendor')
#         #vendor = int(vendor)
#         id = invoice
#         form = AddInvoiceItemForm(request.POST)
#         if form.is_valid():
#             form.instance.invoice_id = invoice
#             form.save()
#             name = form.instance.name
#             try:
#                 item = RetailVendorItemDetail.objects.get(name=name, vendor_id=vendor)
#                 print(name)    
#             except:
#                 print(vendor)
#                 RetailVendorItemDetail.objects.create(
#                     vendor_id = vendor,
#                     name=name,
#                     vendor_part_number = form.instance.vendor_part_number,
#                     description = form.instance.description,
#                     internal_part_number = form.instance.internal_part_number,
#                     high_price = form.instance.unit_cost
#                     )
#         else:
#             print(form.errors)
#         invoice = get_object_or_404(RetailInvoices, id=invoice)
#         items = RetailInvoiceItem.objects.filter(invoice_id = invoice)
#         print(items)
#         #items = 
#         #print(vendor)
#         # context = {
#         #     'invoice': invoice,
#         #     'items': items,
#         # }
#         return redirect ('retail:invoice_detail', id=id)
#     invoice = get_object_or_404(RetailInvoices, id=id)
#     items = RetailInvoiceItem.objects.filter(invoice_id = id)
#     context = {
#         'invoice': invoice,
#         'items': items,
#     }
#     return render(request, 'retail/invoices/detail.html', context)

@login_required
def add_invoice(request):
    form = AddInvoiceForm()
    if request.method == "POST":
        form = AddInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            invoice = form.instance.pk
            return redirect ('retail:invoice_detail', id=invoice)
        else:
            print(form.errors)
        #invoices = RetailInvoices.objects.all().order_by('invoice_date')
        #print(vendor)
        # context = {
        #     'invoices': invoices,
        # }
        
    context = {
        'form': form,
        #'categories': categories
    }
    return render (request, "retail/invoices/add_invoice.html", context)


def add_invoice_item(request, invoice=None, vendor=None):
    if vendor:
        item_id = request.GET.get('name')
        if item_id:
            print(item_id)
            print(vendor)
            try:
                item = get_object_or_404(RetailVendorItemDetail, internal_part_number=item_id, vendor=vendor)
                name = item.name
                ipn = item_id
                vpn = item.vendor_part_number
                description = item.description
                context = {
                    'name': name,
                    'vpn': vpn,
                    'ipn': ipn,
                    'description': description,
                    'vendor':vendor,
                    'invoice':invoice,
                }
                return render (request, "retail/invoices/partials/invoice_item_remainder.html", context)
            except:
                print('sorry')
                item = ''
                form = ''
                vendor = ''
            print(vendor)
            form = AddInvoiceItemForm
            context = {
                'form':form,
                'vendor':vendor,
                'invoice':invoice,
            }
            return render (request, "retail/invoices/partials/invoice_item_remainder.html", context)
    invoice = invoice
    vendor = RetailInvoices.objects.get(id=invoice)
    print(vendor.vendor.name)
    vendor = vendor.vendor.id
    print(vendor)
    #items = RetailInvoiceItem.objects.filter(vendor=vendor)
    items = RetailVendorItemDetail.objects.filter(vendor=vendor)
    form = AddInvoiceItemForm
    context = {
        'items': items,
        'invoice': invoice,
        'vendor': vendor,
        'form': form,
    }
    return render (request, "retail/invoices/partials/add_invoice_item.html", context)

def add_inventory_item(request, vendor=None, invoice=None):
    form = RetailInventoryMasterForm
    if not invoice:
        if request.method == "POST":
            form = RetailInventoryMasterForm(request.POST)
            if form.is_valid():
                form.save()
                pk = form.instance.pk
                item = RetailInventoryMaster.objects.get(pk=pk)
                print(item.pk)
                vendor = item.primary_vendor
                name = item.name
                vpn = item.primary_vendor_part_number
                description = item.description
                invoice = request.POST.get('invoice')
                print(vendor)
                item = RetailVendorItemDetail(vendor=vendor, name=name, vendor_part_number=vpn, description=description, internal_part_number_id=item.pk )
                item.save()
                if invoice:
                    return redirect ('retail:invoice_detail', id=invoice)
                return redirect ('retail:retail_inventory_list')
        context = {
        'form':form,
        'invoice':invoice
        }
        return render (request, "retail/inventory/add_inventory_item.html", context)

    # if request.method == "POST":
    #     invoice = request.POST.get('invoice')
    #     form = RetailInventoryMasterForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         return redirect ('retail:invoice_detail', id=invoice)
    #     else:
    #         print(form.errors)
    context = {
        'form':form,
        'invoice':invoice
    }
    return render (request, "retail/invoices/partials/add_inventory_item.html", context)

def retail_inventory_list(request):
    items = RetailInventoryMaster.objects.all()
    context = {
        'items': items,
    }
    return render (request, "retail/inventory/inventory_list.html", context)

@login_required
def invoice_detail(request, id=None):
    # if request.method == "POST":
        # invoice = request.POST.get('invoice')
        # vendor = request.POST.get('vendor')
        # vendor_part_number = request.POST.get('vendor_part_number')
        # description = request.POST.get('description')
        # unit_cost = request.POST.get('unit_cost')
        # qty = request.POST.get('qty')
        # name = request.POST.get('name')
        # internal_part_number = request.POST.get('internal_part_number')
    if request.method == "POST":
        invoice = request.POST.get('invoice')
        vendor = request.POST.get('vendor')
        #vendor = int(vendor)
        id = invoice
        form = AddInvoiceItemForm(request.POST)
        if form.is_valid():
            form.instance.invoice_id = invoice
            form.save()
            name = form.instance.name
            print(name)
            print(vendor)
            try:
                item = RetailVendorItemDetail.objects.get(name=name, vendor_id=vendor)
            except:
                print('No Item')
            if item:
                print(item.pk)
                high_price = item.high_price
                print(high_price)
                current_price = form.instance.unit_cost
                print(current_price)
                if high_price:
                    high_price = int(high_price)
                if current_price:
                    if not high_price:
                        high_price = 0
                        current_price = Decimal(current_price)
                        RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=current_price, updated=datetime.now())
                        print(3)
                    current_price = int(current_price)
                    if current_price > high_price:
                        current_price = Decimal(current_price)
                        RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=current_price)
                        print(4)            
                # if high_price == 'None':
                #     high_price = 0
                # if current_price == 'None':
                #     current_price = 0
                # if not high_price:
                    
                
                    
            # if not item:
            #     print(vendor)
            #     RetailVendorItemDetail.objects.create(
            #         vendor_id = vendor,
            #         name=name,
            #         vendor_part_number = form.instance.vendor_part_number,
            #         description = form.instance.description,
            #         internal_part_number = form.instance.internal_part_number,
            #         high_price = form.instance.unit_cost
            #         )
        else:
            print(form.errors)
        invoice = get_object_or_404(RetailInvoices, id=invoice)
        items = RetailInvoiceItem.objects.filter(invoice_id = invoice)
        print(items)
        #items = 
        #print(vendor)
        # context = {
        #     'invoice': invoice,
        #     'items': items,
        # }
        return redirect ('retail:invoice_detail', id=id)
    invoice = get_object_or_404(RetailInvoices, id=id)
    items = RetailInvoiceItem.objects.filter(invoice_id = id)
    context = {
        'invoice': invoice,
        'items': items,
    }
    return render(request, 'retail/invoices/detail.html', context)


#######################################################################################################################################

## Needs work


def add_item_to_vendor(request, vendor=None, invoice=None):
    print('vendor')
    print(vendor)
    if request.method == "POST":
        print('something')
        form = RetailVendorItemDetailForm(request.POST)
        if form.is_valid():
            form.save()
            print('valid')
            invoice = request.POST.get('invoice')
            vendor_part_number = request.POST.get('vendor_part_number')
            vendor = request.POST.get('vendor')
            pk = form.instance.pk
            RetailVendorItemDetail.objects.filter(pk=pk).update(vendor=vendor, vendor_part_number=vendor_part_number)
            return redirect ('retail:invoice_detail', id=invoice)
        else:
            print(form.errors)
        #return redirect ('retail:invoice_detail', id=invoice)
        # name = request.POST.get('name')
        # vendor_part_number = request.POST.get('vendor_part_number')
        # internal_part_number = request.POST.get('internal_part_number')
        # invoice = request.POST.get(invoice')
        # 'name', 'vendor_part_number', 'description', 'internal_part_number'
    form = RetailVendorItemDetailForm
    
    #Get all inventory items
    items = RetailInventoryMaster.objects.all()
    list = []
    #Go through inventory. If not matched with a vendor, add to select list
    for x in items:
        try:
            print('part number')
            obj = get_object_or_404(RetailVendorItemDetail, internal_part_number=x.pk, vendor=vendor)
            print(obj)
        except:
            list.append(x)
            print('except')
            print(x.pk)
    print(list)
    context = {
        'form':form,
        'vendor': vendor,
        'invoice': invoice,
        'list':list,
        # 'items':items,
    }
    if not vendor:
        return render (request, "retail/inventory/add_item_to_vendor.html", context)
    return render (request, "retail/invoices/partials/add_item_to_vendor.html", context)


def edit_invoice_item(request, invoice=None, id=None):
    print(id)
    item = RetailInvoiceItem.objects.get(id=id)
    print(item)
    print(item.pk)
    if request.method == "POST":
        invoice = item.invoice_id
        print(invoice)
        #vendor = request.POST.get('vendor')
        form = AddInvoiceItemForm(request.POST)
        if form.is_valid():
            #form.save()
            name = form.instance.name
            vendor_part_number = form.instance.vendor_part_number
            description = form.instance.description
            unit_cost = form.instance.unit_cost
            qty = form.instance.qty
            RetailInvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
            print('IPN')
            print(item.internal_part_number.id)
            print('Vendor')
            print(item.vendor.id)
            # vendor_item = RetailVendorItemDetail.objects.get(internal_part_number=item.internal_part_number.id, vendor=item.vendor.id)
            # print(vendor_item.pk)
            try:
                vendor_item = RetailVendorItemDetail.objects.get(internal_part_number=item.internal_part_number.id, vendor=item.vendor.id)
                print(vendor_item.pk)
            except:
                print('failed')
            if vendor_item:
                high_price = vendor_item.high_price
                print(high_price)
                current_price = form.instance.unit_cost
                print(current_price)
                high_price = int(high_price)
                current_price = int(current_price)
                print('issue')
                if high_price == 'None':
                    hp = 0
                    print(1)
                else:
                    hp = high_price
                print('issue')
                if current_price == 'None':
                    cp = 0
                    print(2)
                else:
                    cp = current_price
                print('issue')
                #updated = datetime.now
                #print(updated)
                if not high_price:
                    RetailVendorItemDetail.objects.filter(pk=vendor_item.pk).update(high_price=cp)
                    print(3)
                if current_price > high_price:
                    print(high_price)
                    print(hp)
                    print(current_price)
                    print(cp)
                    RetailVendorItemDetail.objects.filter(pk=vendor_item.pk).update(high_price=cp, updated=datetime.now()) 
                #RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=cp)
                print(high_price)
                print(hp)
                print(current_price)
                print(cp)
                print('something')
                return redirect ('retail:invoice_detail', id=invoice)
            
        else:
            print(form.errors)

    name = item.name
    vpn = item.vendor_part_number
    description = item.description
    unit_cost = item.unit_cost
    qty = item.qty
    pk = item.pk
    ipn = item.internal_part_number.id
    vendor = item.vendor.id
    #form = AddInvoiceItemForm(instance=item)
    # if request.method == "POST":
    #     invoice = request.POST.get('invoice')
    #     vendor = request.POST.get('vendor')
    #     #vendor = int(vendor)
    #     id = invoice
    #     form = AddInvoiceItemForm(request.POST)
    #     if form.is_valid():
    #         form.instance.invoice_id = invoice
    #         form.save()
    #         name = form.instance.name
    #         try:
    #             item = RetailVendorItemDetail.objects.get(name=name, vendor_id=vendor)
    #             print(item.pk)
    #             high_price = item.high_price
    #             print(high_price)
    #             current_price = form.instance.unit_cost
    #             print(current_price)
    #             if not high_price:
    #                 RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=current_price, updated=datetime.now())
    #             elif current_price > high_price:
    #                 RetailVendorItemDetail.objects.filter(pk=item.pk).update(high_price=current_price, updated=datetime.now())            
    #         except:
    #             print(vendor)
    #             RetailVendorItemDetail.objects.create(
    #                 vendor_id = vendor,
    #                 name=name,
    #                 vendor_part_number = form.instance.vendor_part_number,
    #                 description = form.instance.description,
    #                 internal_part_number = form.instance.internal_part_number,
    #                 high_price = form.instance.unit_cost
    #                 )
    #     else:
    #         print(form.errors)
    item = RetailInvoiceItem.objects.filter(id=id)
    print(item)
    context = {
        'item':item,
        'name':name,
        'vendor':vendor,
        'vpn':vpn,
        'description':description,
        'unit_cost':unit_cost,
        'qty':qty,
        'pk':pk,
        'ipn':ipn,
        #'form':form
    }
    return render (request, "retail/invoices/partials/edit_invoice_item.html", context)
