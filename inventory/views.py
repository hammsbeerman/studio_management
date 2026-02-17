import json
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import OuterRef, Subquery, Q, Count
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .services.ledger import get_on_hand
from .forms import AddVendorForm, RetailCategoryForm, RetailCategoryMarkupForm, InventoryItemPricingForm, InventoryAdjustmentForm, BulkUomUpdateForm, NormalizeMeasurementsForm, UomAuditFilterForm, UomFixActionForm
from .models import Vendor, InventoryQtyVariations, InventoryMaster, OrderOut, Inventory, VendorItemDetail, InventoryLedger, InventoryMerge
from .utils import merged_set_for
from controls.forms import AddItemtoListForm
from controls.models import RetailInventoryCategory
from finance.models import InvoiceItem, AccountsPayable#, AllInvoiceItem
from inventory.services.ledger import (
    get_negative_stock_items,
    get_on_hand,
    get_stock_valuation_for_item,
    get_stock_alerts,
    get_on_hand,
    record_inventory_movement
)
from inventory.services.measurement_normalize import (
    build_item_queryset,
    normalize_measurements_for_items
)
from inventory.services.uom_audit import (
    set_base_uom,
    set_default_receive_uom,
    set_default_sell_uom,
)
from inventory.services.pricing import compute_retail_price
from onlinestore.models import StoreItemDetails
from retail.models import RetailSaleLine


#from inventory.models import Inventory

# Create your views here.

# @login_required
# def inv_list(request):
#     pass

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


# --------- Inventory Cleanup ----------------------------------------------------------------
@login_required
@permission_required("inventory.view_inventorymaster", raise_exception=True)
def inventory_cleanup_overview(request):
    """
    Dashboard showing likely duplicate InventoryMaster items,
    grouped by (vendor + vendor PN) and (vendor + name).

    Optional GET params:
      - vendor: vendor id filter
      - mode, cluster_vendor, cluster_key: used to show a focused cluster for merging.
    """
    vendor_filter = request.GET.get("vendor")
    base_qs = (
        InventoryMaster.objects
        .filter(active=True)
        .select_related("primary_vendor", "primary_base_unit")
    )

    if vendor_filter:
        try:
            vendor_id = int(vendor_filter)
            base_qs = base_qs.filter(primary_vendor_id=vendor_id)
        except (TypeError, ValueError):
            vendor_filter = None  # ignore bad filter

    # --- Group 1: duplicates by vendor + vendor PN ---
    vendor_pn_dupes = (
        base_qs.exclude(primary_vendor__isnull=True)
        .exclude(primary_vendor_part_number__isnull=True)
        .exclude(primary_vendor_part_number__exact="")
        .values("primary_vendor_id", "primary_vendor__name", "primary_vendor_part_number")
        .annotate(item_count=Count("id"))
        .filter(item_count__gt=1)
        .order_by("primary_vendor__name", "primary_vendor_part_number")
    )

    # --- Group 2: duplicates by vendor + name ---
    name_dupes = (
        base_qs.exclude(primary_vendor__isnull=True)
        .values("primary_vendor_id", "primary_vendor__name", "name")
        .annotate(item_count=Count("id"))
        .filter(item_count__gt=1)
        .order_by("primary_vendor__name", "name")
    )

    # --- Optional: focused cluster detail for merge UI ---
    cluster_mode = request.GET.get("mode")          # "vendorpn" or "name"
    cluster_vendor = request.GET.get("cluster_vendor")
    cluster_key = request.GET.get("cluster_key")

    cluster_items = None
    if cluster_mode and cluster_vendor and cluster_key:
        try:
            v_id = int(cluster_vendor)
        except (TypeError, ValueError):
            v_id = None

        if v_id:
            if cluster_mode == "vendorpn":
                cluster_qs = (
                    base_qs.filter(
                        primary_vendor_id=v_id,
                        primary_vendor_part_number=cluster_key,
                    )
                    .select_related("primary_vendor", "primary_base_unit")
                    .prefetch_related("inventoryqtyvariations_set", "ledger_entries", "retail_lines")
                )
            elif cluster_mode == "name":
                cluster_qs = (
                    base_qs.filter(
                        primary_vendor_id=v_id,
                        name=cluster_key,
                    )
                    .select_related("primary_vendor", "primary_base_unit")
                    .prefetch_related("inventoryqtyvariations_set", "ledger_entries", "retail_lines")
                )
            else:
                cluster_qs = InventoryMaster.objects.none()

            # Build a list of dicts with precomputed stats
            cluster_items = []
            for item in cluster_qs:
                cluster_items.append({
                    "item": item,
                    "onhand": get_on_hand(item),
                    "ledger_count": item.ledger_entries.count(),
                    "retail_count": item.retail_lines.count(),
                })

    vendors = Vendor.objects.order_by("name")

    context = {
        "vendors": vendors,
        "vendor_filter": vendor_filter,
        "vendor_pn_dupes": vendor_pn_dupes,
        "name_dupes": name_dupes,
        "cluster_mode": cluster_mode,
        "cluster_vendor": cluster_vendor,
        "cluster_key": cluster_key,
        "cluster_items": cluster_items,  # list of {item, onhand, ledger_count, retail_count}
    }
    return render(request, "inventory/cleanup_overview.html", context)


@login_required
@permission_required("inventory.change_inventorymaster", raise_exception=True)
@transaction.atomic
def merge_inventory_items(request):
    """
    POST-only view that merges duplicate InventoryMaster items into a chosen 'keeper'.

    Expected POST params:
      - keeper_id: the canonical item
      - merge_ids: list of ids to merge INTO keeper (duplicates)
      - redirect_url: where to go after (usually cleanup_overview with cluster params)
    """
    if request.method != "POST":
        return redirect("inventory:inventory_cleanup_overview")

    keeper_id = request.POST.get("keeper_id")
    merge_ids = request.POST.getlist("merge_ids")
    redirect_url = request.POST.get("redirect_url") or reverse(
        "inventory:inventory_cleanup_overview"
    )

    try:
        keeper = InventoryMaster.objects.select_for_update().get(pk=keeper_id)
    except (InventoryMaster.DoesNotExist, ValueError, TypeError):
        messages.error(request, "Invalid keeper item.")
        return redirect(redirect_url)

    merge_qs = InventoryMaster.objects.select_for_update().filter(pk__in=merge_ids)
    merge_items = [m for m in merge_qs if m.pk != keeper.pk]

    if not merge_items:
        messages.warning(request, "No items selected to merge.")
        return redirect(redirect_url)

    for src in merge_items:
        # 1) Update all references from src → keeper

        InventoryLedger.objects.filter(inventory_item=src).update(
            inventory_item=keeper
        )
        Inventory.objects.filter(internal_part_number=src).update(
            internal_part_number=keeper
        )
        VendorItemDetail.objects.filter(internal_part_number=src).update(
            internal_part_number=keeper
        )
        RetailSaleLine.objects.filter(inventory=src).update(inventory=keeper)
        InvoiceItem.objects.filter(internal_part_number=src).update(
            internal_part_number=keeper
        )
        StoreItemDetails.objects.filter(item=src).update(item=keeper)

        # 2) Move variations (clone if not already present)
        existing_variations = set(
            InventoryQtyVariations.objects.filter(inventory=keeper).values_list(
                "variation_id", "variation_qty"
            )
        )

        for v in InventoryQtyVariations.objects.filter(inventory=src):
            key = (v.variation_id, v.variation_qty)
            if key not in existing_variations:
                v.pk = None
                v.inventory = keeper
                v.save()

        # 3) Record merge history
        InventoryMerge.objects.get_or_create(
            from_item=src,
            to_item=keeper,
            defaults={
                "reason": "Merged via inventory cleanup tool",
                "created_by": request.user if request.user.is_authenticated else None,
            },
        )

        # 4) Archive the duplicate instead of deleting (because InventoryMerge uses PROTECT)
        src.active = False
        src.save()

    messages.success(
        request,
        f"Merged {len(merge_items)} duplicate item(s) into {keeper.name} (#{keeper.id}).",
    )
    return redirect(redirect_url)


# --- Item units & variations editor -----------------------------------------


@login_required
@permission_required("inventory.change_inventorymaster", raise_exception=True)
def item_units_editor(request, pk):
    """
    Simple editor for:
      - InventoryMaster.primary_base_unit
      - InventoryMaster.units_per_base_unit
      - Existing InventoryQtyVariations.variation_qty
    (No add/remove yet; just cleaning up existing data.)
    """
    item = get_object_or_404(
        InventoryMaster.objects.select_related("primary_base_unit"), pk=pk
    )
    variations = InventoryQtyVariations.objects.select_related("variation").filter(
        inventory=item
    )

    if request.method == "POST":
        # Base unit + units_per_base_unit
        base_unit_id = request.POST.get("primary_base_unit") or None
        units_per = request.POST.get("units_per_base_unit") or None

        if base_unit_id:
            try:
                item.primary_base_unit_id = int(base_unit_id)
            except (TypeError, ValueError):
                pass

        if units_per:
            try:
                item.units_per_base_unit = Decimal(units_per)
            except (TypeError, ValueError):
                item.units_per_base_unit = None
        else:
            item.units_per_base_unit = None

        item.save()

        # Variation quantities
        for v in variations:
            key = f"variation_{v.id}_qty"
            val = request.POST.get(key)
            if val:
                try:
                    v.variation_qty = Decimal(val)
                    v.save()
                except (TypeError, ValueError):
                    # ignore bad inputs for that row
                    continue

        messages.success(request, "Units and variations updated.")
        return redirect(
            reverse("inventory:item_units_editor", kwargs={"pk": item.pk})
        )

    context = {
        "item": item,
        "variations": variations,
    }
    return render(request, "inventory/item_units_editor.html", context)


# --- Duplicate check for new items (HTMX-friendly partial) ------------------


@login_required
def search_existing_items(request):
    """
    Lightweight search endpoint to help avoid new duplicates.

    GET params:
      - vendor: vendor id
      - term: free-text (name / description)
      - pn: vendor part number
    """
    vendor_id = request.GET.get("vendor")
    term = (request.GET.get("term") or "").strip()
    pn = (request.GET.get("pn") or "").strip()

    qs = InventoryMaster.objects.select_related("primary_vendor", "primary_base_unit")

    if vendor_id:
        try:
            qs = qs.filter(primary_vendor_id=int(vendor_id))
        except (TypeError, ValueError):
            pass

    q_filter = Q()

    if pn:
        q_filter |= Q(primary_vendor_part_number__iexact=pn)
        q_filter |= Q(primary_vendor_part_number__icontains=pn)

    if term:
        q_filter |= Q(name__icontains=term) | Q(description__icontains=term)

    if not q_filter:
        items = []
    else:
        items = (
            qs.filter(q_filter)
            .order_by("primary_vendor__name", "name")
            .distinct()[:10]
        )

    context = {
        "items": items,
        "term": term,
        "pn": pn,
    }
    return render(
        request,
        "inventory/partials/search_existing_items.html",
        context,
    )

@login_required
def bulk_uom_admin(request):
    from decimal import Decimal
    from django.contrib import messages
    from django.shortcuts import render

    import inspect
    from inventory.services import uom_bulk

    print("uom_bulk.build_item_queryset:", uom_bulk.build_item_queryset, inspect.getsourcefile(uom_bulk.build_item_queryset))
    print("local build_item_queryset symbol:", globals().get("build_item_queryset"))

    form = BulkUomUpdateForm(request.POST or None)
    preview_items = []
    result = None

    if request.method == "POST" and form.is_valid():
        measurement = form.cleaned_data["measurement"]
        variation_qty = form.cleaned_data["variation_qty"] or Decimal("1.0000")
        name_contains = (form.cleaned_data["name_contains"] or "").strip()
        vendor = form.cleaned_data["vendor"]
        dry_run = not bool(form.cleaned_data["apply"])

        item_qs = uom_bulk.build_item_queryset(
            only_active=True,
            name_contains=name_contains,
            vendor_id=vendor.id if vendor else None,
        )

        preview_items = list(item_qs.order_by("name")[:200])

        result = uom_bulk.bulk_set_item_uom(
            item_qs=item_qs,
            measurement=measurement,
            variation_qty=variation_qty,
            set_as_base=form.cleaned_data["set_as_base"],
            set_as_default_sell=form.cleaned_data["set_as_default_sell"],
            set_as_default_receive=form.cleaned_data["set_as_default_receive"],
            dry_run=dry_run,
        )

        if dry_run:
            messages.info(request, f"Dry run: matched={result.matched}, would_change={result.changed}, would_create={result.created}.")
        else:
            messages.success(request, f"Applied: matched={result.matched}, changed={result.changed}, created={result.created}, skipped={result.skipped}.")

    return render(request, "inventory/uom_bulk_admin.html", {"form": form, "preview_items": preview_items, "result": result})


@login_required
def uom_normalize_admin(request):
    form = NormalizeMeasurementsForm(request.POST or None)
    result = None

    if request.method == "POST" and form.is_valid():
        vendor = form.cleaned_data["vendor"]
        only_active = bool(form.cleaned_data["only_active"])
        name_contains = (form.cleaned_data["name_contains"] or "").strip()

        do_each = bool(form.cleaned_data["do_each"])
        do_sht = bool(form.cleaned_data["do_sht"])
        include_primary = bool(form.cleaned_data["include_primary_base_unit"])

        fix_missing_base_uom = bool(form.cleaned_data["fix_missing_base_uom"])
        fix_missing_defaults = bool(form.cleaned_data["fix_missing_defaults"])

        dry_run = not bool(form.cleaned_data["apply"])

        item_qs = build_item_queryset(
            only_active=only_active,
            vendor_id=vendor.id if vendor else None,
            name_contains=name_contains,
        )

        result = normalize_measurements_for_items(
            item_qs=item_qs,
            do_each=do_each,
            do_sht=do_sht,
            include_primary_base_unit=include_primary,
            fix_missing_base_uom=fix_missing_base_uom,          # ✅ NEW
            fix_missing_defaults=fix_missing_defaults,          # ✅ NEW
            dry_run=dry_run,
        )

        if result.errors:
            for e in result.errors:
                messages.error(request, e)
        else:
            if dry_run:
                messages.info(request, "Dry run preview only (no DB changes).")
            else:
                messages.success(request, "Normalization applied.")

    return render(request, "inventory/uom_normalize_admin.html", {"form": form, "result": result})


# @login_required
# def uom_audit_admin(request):
#     form = UomAuditFilterForm(request.GET or None)
#     result = None

#     if form.is_valid():
#         vendor = form.cleaned_data.get("vendor")
#         result = audit_uoms(
#             only_active=bool(form.cleaned_data.get("only_active")),
#             vendor_id=vendor.id if vendor else None,
#             name_contains=(form.cleaned_data.get("name_contains") or "").strip(),
#             limit=500,
#         )

#     return render(
#         request,
#         "inventory/uom_audit_admin.html",
#         {"form": form, "result": result},
#     )


# @login_required
# def uom_audit_apply(request):
#     if request.method != "POST":
#         return HttpResponseRedirect(reverse("inventory:uom_audit_admin"))

#     form = UomFixActionForm(request.POST)
#     if not form.is_valid():
#         messages.error(request, "Invalid request.")
#         return HttpResponseRedirect(reverse("inventory:uom_audit_admin"))

#     item = get_object_or_404(InventoryMaster, pk=form.cleaned_data["item_id"])
#     action = form.cleaned_data["action"]
#     variation_id = form.cleaned_data.get("variation_id")

#     try:
#         if action == "set_base":
#             if not variation_id:
#                 raise ValueError("Missing variation_id")
#             set_base_uom(item=item, variation_id=int(variation_id))
#             messages.success(request, f"{item.name}: base UOM updated.")
#         elif action == "set_default_sell":
#             if not variation_id:
#                 raise ValueError("Missing variation_id")
#             set_default_sell_uom(item=item, variation_id=int(variation_id))
#             messages.success(request, f"{item.name}: default SELL UOM updated.")
#         elif action == "set_default_receive":
#             if not variation_id:
#                 raise ValueError("Missing variation_id")
#             set_default_receive_uom(item=item, variation_id=int(variation_id))
#             messages.success(request, f"{item.name}: default RECEIVE UOM updated.")
#         elif action == "normalize_defaults":
#             normalize_missing_defaults(item=item)
#             messages.success(request, f"{item.name}: defaults normalized.")
#         else:
#             messages.error(request, "Unknown action.")
#     except Exception as e:
#         messages.error(request, f"Failed: {e}")

#     return HttpResponseRedirect(reverse("inventory:uom_audit_admin"))