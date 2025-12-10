import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import OuterRef, Subquery
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
from controls.forms import AddItemtoListForm
from controls.models import RetailInventoryCategory
from .forms import AddVendorForm, RetailCategoryForm, RetailCategoryMarkupForm, InventoryItemPricingForm, InventoryAdjustmentForm
from .models import Vendor, InventoryQtyVariations, InventoryMaster, OrderOut, Inventory
from finance.models import InvoiceItem, AccountsPayable#, AllInvoiceItem
from .utils import merged_set_for
from inventory.services.pricing import compute_retail_price
from inventory.services.ledger import (
    get_negative_stock_items,
    get_on_hand,
    get_stock_valuation_for_item,
    get_stock_alerts,
    get_on_hand,
)
#from inventory.models import Inventory

# Create your views here.

@login_required
def list(request):
    pass

@login_required
def add_vendor(request):
    form = AddVendorForm()
    if request.htmx:
        if request.method == "POST":
            form = AddVendorForm(request.POST)
            pk = request.POST.get('item')
            cat = request.POST.get('cat')
            if form.is_valid():
                form.save()
                context = {
                    'pk': pk,
                    'cat': cat,
                }
                return redirect('workorders:edit_orderout_item', pk=pk, cat=cat)
        pk = request.GET.get('item')
        cat = request.GET.get('cat')
        print(pk)
        print(cat)
        context = {
                'form': form,
                'pk': pk,
                'cat': cat,
                #'categories': categories
            }
        return render (request, "inventory/vendors/add_vendor_modal.html", context)
    if request.method == "POST":
        form = AddVendorForm(request.POST)
        if form.is_valid():
            form.save()
        vendors = Vendor.objects.all().order_by('name')
        #print(vendor)
        context = {
            'vendors': vendors,
        }
        return render (request, "inventory/vendors/list.html", context)
    context = {
        'form': form,
        #'categories': categories
    }
    return render (request, "inventory/vendors/add_vendor.html", context)


@login_required
def vendor_list(request, vendor=None):
    if not vendor:
        vendor = Vendor.objects.all().order_by("name")
        print('vendors')
        context = {
            'vendors': vendor,
        }
        return render(request, 'inventory/vendors/list.html', context)
    else:
        if vendor == 'All':
            vendor = Vendor.objects.all().order_by("name")
        if vendor == 'Retail':
            vendor = Vendor.objects.filter(retail_vendor=1).order_by("name")
        elif vendor == 'Supply':
            vendor = Vendor.objects.filter(supplier=1).order_by("name")
        elif vendor == 'Inventory':
            vendor = Vendor.objects.filter(inventory_vendor=1).order_by("name")
        elif vendor == 'NonInventory':
            vendor = Vendor.objects.filter(non_inventory_vendor=1).order_by("name")
        elif vendor == 'Other':
            vendor = Vendor.objects.filter(supplier=0, retail_vendor=0, inventory_vendor=0, non_inventory_vendor=0).order_by("name")
        print('vendors')
        context = {
            'vendors': vendor,
        }
        return render(request, 'inventory/vendors/partials/vendor_list.html', context)

@login_required
def vendor_detail(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    if vendor.supplier == 1:
        supplier = 'True'
    else:
        supplier = 'False'
    if vendor.retail_vendor == 1:
        retail = 'True'
    else:
        retail = 'False'
    if vendor.inventory_vendor == 1:
        inventory_vendor = 'True'
    else:
        inventory_vendor = 'False'
    if vendor.non_inventory_vendor == 1:
        non_inventory_vendor = 'True'
    else:
        non_inventory_vendor = 'False'
    orderout = OrderOut.objects.filter(vendor=id)
    context = {
        'orderout': orderout,
        'non_inventory_vendor': non_inventory_vendor,
        'inventory_vendor': inventory_vendor,
        'retail': retail,
        'supplier':supplier,
        'vendor': vendor,
    }
    return render(request, 'inventory/vendors/detail.html', context)

@login_required
def edit_vendor(request, id):
    if request.method == "POST":
        vendor = Vendor.objects.get(id=id)
        print(id)
        form = AddVendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
        vendors = Vendor.objects.all().order_by('name')
        #print(vendor)
        context = {
            'vendors': vendors,
        }
        return render (request, "inventory/vendors/list.html", context)
    obj = get_object_or_404(Vendor, id=id)
    form = AddVendorForm(instance=obj)
    vendor = id
    context = {
        'form':form,
        'vendor':vendor,
    }
    return render(request, 'inventory/vendors/edit_vendor.html', context)


def item_variations(request):
    items = InventoryQtyVariations.objects.all()
    unique_list = []
    list = []
    for x in items:
        # check if exists in unique_list or not
        if x.inventory not in list:
            unique_list.append(x)
            list.append(x.inventory)
    print(unique_list)
    context = {
        #'group':group,
        'unique_list':unique_list
    }
    return render(request, 'inventory/items/view_variations.html', context)

def item_variation_details(request, id=None):
    print(id)
    variations = InventoryQtyVariations.objects.filter(inventory=id)
    print(variations)
    context = {
        'variations':variations
    }
    return render(request, 'inventory/items/view_variation_details.html', context)

# def item_detail(request):
#     items = InventoryMaster.objects.all()
#     context = {
#         'items':items,
#     }
#     return render(request, 'inventory/items/item_details', context)

def item_details(request, id=None):
    id = request.GET.get('name')
    #items = InventoryMaster.objects.all()
    items = (
        InventoryMaster.objects
        .filter(active=True)
        .prefetch_related("inventory_set")  # default reverse name from Inventory FK
        .order_by("name")
    )
    
    
    if request.method == "POST":
        id = request.POST.get('master_id')
        obj = get_object_or_404(Inventory, internal_part_number=id)
        form = AddItemtoListForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
        item = InvoiceItem.objects.filter(internal_part_number=id).order_by('-invoice__invoice_date')
        for x in item:
            print(x.invoice.invoice_number)
            print(x.invoice.invoice_date)
        master = InventoryMaster.objects.get(pk=id)
        context = {
            'items':items,
            'form':form,
            'item':item,
            'master':master,
        }
        return render(request, 'inventory/items/item_details_updated.html', context)
    print(id)
    if id:
        item = InvoiceItem.objects.filter(internal_part_number=id).order_by('-invoice__invoice_date')
        for x in item:
            print(x.invoice.invoice_number)
            print(x.invoice.invoice_date)
        master = InventoryMaster.objects.get(pk=id)


        obj = get_object_or_404(Inventory, internal_part_number=id)
        form = AddItemtoListForm(instance=obj)





        context = {
            #'item_history':item_history,
            'form':form,
            'item':item,
            'master':master,
        }
        return render (request, "inventory/items/partials/item_details.html", context)
    context = {
        'items':items,
    }
    return render(request, 'inventory/items/item_details.html', context)


def inventory_detail(request, pk):
    item = get_object_or_404(InventoryMaster, pk=pk)
    ids = merged_set_for(item)

    # If your purchase history lives in finance.InvoiceItem or finance.AllInvoiceItem:
    # Adjust names/fields to match your project (common name: InvoiceItem with FK "inventory" or "item")
    from finance.models import InvoiceItem, AllInvoiceItem  # if present
    history = InvoiceItem.objects.filter(inventory_id__in=ids).order_by("-purchase_date")
    # or: history = InvoiceItem.objects.filter(item_id__in=ids)

    return render(request, "inventory/detail.html", {"item": item, "history": history})






























# @login_required
# def add_inventory_item(request):
#     form = AddInventoryItemForm(request.POST or None)
#     item = Inventory.objects.all().order_by('name')
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             #updated = timezone.now()
#             if form.is_valid():
#                 item = request.POST.get('item')
#                 obj = form.save(commit=False)
#                 price_per_m = obj.price_per_m
#                 price_per_m = float(price_per_m)
#                 price_per_m = Decimal.from_float(price_per_m)
#                 price_per_m = round(price_per_m, 2)
#                 print(obj.invoice_date)
#                 #price_per_m = int(price_per_m)
#                 price_ea = price_per_m / 1000
#                 print(price_per_m)
#                 print(price_ea)
#                 #item = get_object_or_404(Inventory, pk=test)
#                 #print (item.name)
#                 obj.save()
#                 Inventory.objects.filter(pk=item).update(price_per_m=price_per_m, unit_cost=price_ea, updated=obj.invoice_date)
#             else:
#                 print(form.errors)


#                 #messages.success(request, "Record Added...")
#             form = AddInventoryItemForm()
#             item = Inventory.objects.all().order_by('name')
#             context = {
#                 'form':form,
#                 'item':item
#             }
#             #return redirect('inventory:add_inventory_item', context)
#             return render(request, 'inventory/items/add_inventory_item.html', context)

#         context = {
#             'form':form,
#             'item':item
#         }
#         return render(request, 'inventory/items/add_inventory_item.html', context)
#     else:
#         messages.success(request, "You must be logged in")
#         return redirect('home')



















#Below this is solely for testing API data without DRF

def inventory_list(request):
    """
    Simple JSON endpoint for InventoryMaster, for testing.

    GET:
        Returns {"inventory": [{id, name, description}, ...]}

    POST:
        Accepts JSON body with at least {"name": "..."} and optional
        "description". Creates a minimal InventoryMaster row and
        returns it as JSON.
    """
    if request.method == "GET":
        qs = InventoryMaster.objects.all().order_by("name")
        data = [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
            }
            for item in qs
        ]
        return JsonResponse({"inventory": data})

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        name = (payload.get("name") or "").strip()
        description = (payload.get("description") or "").strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        item = InventoryMaster.objects.create(
            name=name,
            description=description,
            primary_vendor=None,
            primary_base_unit=None,
            non_inventory=False,
        )

        return JsonResponse(
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
            },
            status=201,
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)
        
#def new_inventory_list(request)


# class InventoryCreate(generics.ListCreateAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

# class InventoryPRUD(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer
#     lookup_field = "pk"

# class InventoryListAPIView(generics.ListAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

# class InventoryDetailAPIView(generics.RetrieveAPIView):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

# class InventoryViewSet(viewsets.ModelViewSet):
#     queryset = Inventory.objects.all()
#     serializer_class = InventorySerializer

@login_required
def retail_pricing_admin(request):
    """
    Retail pricing admin:

    - Left sidebar:
        * All real RetailInventoryCategory rows
        * A virtual 'Uncategorized' bucket (items with no retail_category)
    - Right panel:
        * Items for the selected category or 'Uncategorized'
        * Per-item overrides (retail_price, markup %, markup $) with HTMX autosave

    POST actions:
        * add_category
        * update_category_markup
        * bulk_move_items
        * update_item_pricing
    """

    # ------------------------------------------------------------------
    # Categories for sidebar
    # ------------------------------------------------------------------
    categories = RetailInventoryCategory.objects.order_by("name")

    # ------------------------------------------------------------------
    # Category filter: real ID or 'uncategorized'
    # ------------------------------------------------------------------
    category_filter = request.GET.get("category") or ""
    search = request.GET.get("q") or ""

    is_uncategorized = category_filter == "uncategorized"
    current_category = None

    if category_filter and not is_uncategorized:
        try:
            current_category = RetailInventoryCategory.objects.get(pk=category_filter)
        except RetailInventoryCategory.DoesNotExist:
            current_category = None
            category_filter = ""
            is_uncategorized = False

    # ------------------------------------------------------------------
    # Helper for decimals
    # ------------------------------------------------------------------
    def _dec_or_none(val):
        if val is None or val == "":
            return None
        try:
            return Decimal(str(val))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # POST actions
    # ------------------------------------------------------------------
    if request.method == "POST":
        action = request.POST.get("action")

        # 1) Add new category
        if action == "add_category":
            form = RetailCategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Category added.")
            else:
                messages.error(request, "Please fix errors in the category form.")
            return redirect("inventory:retail_pricing_admin")

        # 2) Update category markup (percent / flat)
        if action == "update_category_markup":
            cat_id = request.POST.get("category_id")
            try:
                cat = RetailInventoryCategory.objects.get(pk=cat_id)
            except RetailInventoryCategory.DoesNotExist:
                messages.error(request, "Category not found.")
                return redirect("inventory:retail_pricing_admin")

            cat.default_markup_percent = _dec_or_none(
                request.POST.get("default_markup_percent")
            )
            cat.default_markup_flat = _dec_or_none(
                request.POST.get("default_markup_flat")
            )
            cat.save(update_fields=["default_markup_percent", "default_markup_flat"])

            # 🔹 HTMX: just save and do NOT swap any HTML (avoid nesting full page)
            if request.headers.get("HX-Request") == "true":
                return HttpResponse(status=204)

            # Non-HTMX fallback
            messages.success(request, f"Markup updated for {cat.name}.")
            return redirect(f"{request.path}?category={cat.id}")

        # 3) Bulk-move items between categories
        if action == "bulk_move_items":
            source_id = request.POST.get("source_category") or None
            target_id = request.POST.get("target_category") or None

            if not target_id:
                messages.error(request, "Please choose a target category.")
                return redirect("inventory:retail_pricing_admin")

            try:
                target_cat = RetailInventoryCategory.objects.get(pk=target_id)
            except RetailInventoryCategory.DoesNotExist:
                messages.error(request, "Target category not found.")
                return redirect("inventory:retail_pricing_admin")

            items_qs = InventoryMaster.objects.filter(active=True, retail=True)

            # Source: "uncategorized" → items with no retail_category
            if source_id == "uncategorized":
                items_qs = items_qs.filter(retail_category__isnull=True)
            elif source_id:
                items_qs = items_qs.filter(retail_category_id=source_id)

            count = items_qs.update(retail_category=target_cat)
            messages.success(
                request,
                f"Moved {count} item(s) to category '{target_cat.name}'.",
            )
            return redirect("inventory:retail_pricing_admin")

        # 4) Per-item pricing updates (HTMX autosave + normal POST)
        if action == "update_item_pricing":
            item_id = request.POST.get("item_id")
            try:
                item = InventoryMaster.objects.get(pk=item_id)
            except InventoryMaster.DoesNotExist:
                messages.error(request, "Item not found.")
                return redirect("inventory:retail_pricing_admin")

            # Optional category change per item (if you later add a select)
            cat_id = request.POST.get("retail_category")
            if cat_id == "":
                item.retail_category = None
            elif cat_id:
                try:
                    item.retail_category = RetailInventoryCategory.objects.get(pk=cat_id)
                except RetailInventoryCategory.DoesNotExist:
                    # ignore bad category
                    pass

            # Hard-set retail price override
            item.retail_price = _dec_or_none(request.POST.get("retail_price"))

            # Item-specific markup overrides
            item.retail_markup_percent = _dec_or_none(
                request.POST.get("retail_markup_percent")
            )
            item.retail_markup_flat = _dec_or_none(
                request.POST.get("retail_markup_flat")
            )

            item.save(
                update_fields=[
                    "retail_category",
                    "retail_price",
                    "retail_markup_percent",
                    "retail_markup_flat",
                ]
            )

            # Recompute effective price for this item
            item.computed_retail_price = compute_retail_price(item)

            # HTMX row replace: return updated row only
            if request.headers.get("HX-Request") == "true":
                category_param = (
                    request.GET.get("category")
                    or (
                        "uncategorized"
                        if item.retail_category_id is None
                        else str(item.retail_category_id)
                    )
                )
                return render(
                    request,
                    "inventory/partials/retail_pricing_item_row.html",
                    {
                        "item": item,
                        "current_category": item.retail_category,
                        "category_param": category_param,
                        "search": request.GET.get("q") or "",
                        "categories": RetailInventoryCategory.objects.order_by("name"),
                    },
                )

            # Non-HTMX fallback: redirect back to current view
            messages.success(request, f"Pricing updated for '{item.name}'.")
            if current_category:
                return redirect(f"{request.path}?category={current_category.id}&q={search}")
            if is_uncategorized:
                return redirect(f"{request.path}?category=uncategorized&q={search}")
            return redirect("inventory:retail_pricing_admin")

        # Unknown action
        messages.error(request, "Unknown action.")
        return redirect("inventory:retail_pricing_admin")

    # ------------------------------------------------------------------
    # GET: build item list only if a category or 'uncategorized' is selected
    # ------------------------------------------------------------------
    page_obj = None
    if current_category or is_uncategorized:
        items = InventoryMaster.objects.filter(active=True, retail=True)

        if current_category:
            items = items.filter(retail_category=current_category)
        elif is_uncategorized:
            items = items.filter(retail_category__isnull=True)

        if search:
            items = items.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(primary_vendor_part_number__icontains=search)
            )

        # Fix UnorderedObjectListWarning
        items = items.order_by("name", "id")

        paginator = Paginator(items, 50)
        page = request.GET.get("page")
        page_obj = paginator.get_page(page)

        for item in page_obj.object_list:
            item.computed_retail_price = compute_retail_price(item)

    # ------------------------------------------------------------------
    # Category form + context
    # ------------------------------------------------------------------
    new_category_form = RetailCategoryForm()

    context = {
        "categories": categories,
        "new_category_form": new_category_form,
        "page_obj": page_obj,
        "category_filter": category_filter,
        "current_category": current_category,
        "is_uncategorized": is_uncategorized,
        "search": search,
    }
    return render(request, "inventory/retail_pricing_admin.html", context)

@login_required
def negative_stock_report(request):
    """
    InventoryMaster-based negative/low stock report.

    - Uses get_on_hand(master) for each InventoryMaster
    - Filters by on_hand <= threshold
    - Paginates results
    """
    raw_threshold = (request.GET.get("threshold") or "").strip() or "0"
    try:
        threshold = Decimal(raw_threshold)
    except Exception:
        threshold = Decimal("0")

    masters = (
        InventoryMaster.objects
        .filter(non_inventory=False)
        .order_by("name", "id")
    )

    rows = []
    for master in masters:
        on_hand = get_on_hand(master)
        if on_hand <= threshold:
            rows.append({"master": master, "on_hand": on_hand})

    paginator = Paginator(rows, 50)  # adjust page size if you want
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "threshold": threshold,
        "page_obj": page_obj,
    }
    return render(request, "inventory/negative_stock_report.html", context)

@login_required
def stock_valuation_report(request):
    """
    InventoryMaster-based valuation report.

    - Only non_inventory=False items
    - Uses get_on_hand(master) and master.unit_cost
    - Paginates results
    """
    masters = (
        InventoryMaster.objects
        .filter(non_inventory=False)
        .select_related("primary_vendor", "primary_base_unit")
        .order_by("name", "id")
    )

    rows = []
    total_value = Decimal("0")

    for master in masters:
        on_hand = get_on_hand(master)
        unit_cost = master.unit_cost or Decimal("0")
        value = (on_hand * unit_cost).quantize(Decimal("0.0001"))
        rows.append(
            {
                "master": master,
                "on_hand": on_hand,
                "unit_cost": unit_cost,
                "value": value,
            }
        )
        total_value += value

    paginator = Paginator(rows, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_value": total_value,
    }
    return render(request, "inventory/stock_valuation_report.html", context)

@login_required
def master_inventory_modal(request, pk):
    """
    Small modal showing all Inventory rows under a given InventoryMaster.
    """
    master = get_object_or_404(InventoryMaster, pk=pk)
    inventories = (
        Inventory.objects
        .filter(internal_part_number=master)
        .order_by("vendor_part_number", "id")
    )

    context = {
        "master": master,
        "inventories": inventories,
    }
    return render(request, "inventory/modals/master_inventory_modal.html", context)

@login_required
@permission_required("inventory.change_inventorymaster", raise_exception=True)
def inventory_adjust(request):
    """
    Simple front-end inventory adjustment form.

    - Positive qty_delta => add stock
    - Negative qty_delta => remove stock
    - Writes to InventoryLedger via record_inventory_movement
    """
    initial_item = None
    item_id = request.GET.get("item")
    if item_id:
        try:
            initial_item = InventoryMaster.objects.get(pk=item_id)
        except InventoryMaster.DoesNotExist:
            initial_item = None

    if request.method == "POST":
        form = InventoryAdjustmentForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data["inventory_item"]
            qty_delta = form.cleaned_data["qty_delta"]
            note = form.cleaned_data["note"] or "Manual inventory adjustment"

            # On-hand before
            try:
                before_on_hand = get_on_hand(item)
            except Exception:
                before_on_hand = None

            # Write ledger entry
            record_inventory_movement(
                inventory_item=item,
                qty_delta=Decimal(qty_delta),
                source_type="ADJUSTMENT",
                source_id=None,
                note=f"{note} (by {request.user})",
            )

            # On-hand after
            try:
                after_on_hand = get_on_hand(item)
            except Exception:
                after_on_hand = None

            if before_on_hand is not None and after_on_hand is not None:
                messages.success(
                    request,
                    f"Adjusted {item} by {qty_delta}. On hand: {before_on_hand} → {after_on_hand}.",
                )
            else:
                messages.success(
                    request,
                    f"Adjusted {item} by {qty_delta}.",
                )

            # Redirect to clear POST
            return redirect(reverse("inventory:inventory_adjust"))
    else:
        form = InventoryAdjustmentForm(
            initial={"inventory_item": initial_item} if initial_item else None
        )

    context = {
        "form": form,
    }
    return render(request, "inventory/inventory_adjust.html", context)