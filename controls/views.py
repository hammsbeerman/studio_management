from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Max, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from customers.models import Customer, ShipTo
from finance.models import InvoiceItem, Krueger_Araging
from inventory.models import (
    Inventory,
    InventoryMaster,
    InventoryPricingGroup,
    InventoryQtyVariations,
    Vendor,
    VendorItemDetail,
)
from workorders.models import Workorder

from .forms import (
    AddSetPriceCategoryForm,
    AddSetPriceItemForm,
    CategoryForm,
    SubCategoryForm,
)
from .models import Category, GroupCategory, Measurement, SetPriceCategory, SubCategory


# -------------------------------------------------------------------
# Simple pages
# -------------------------------------------------------------------
@login_required
def home(request):
    return render(request, "controls/utilities.html")


@login_required
def utilities(request):
    return render(request, "controls/utilities.html")


def special_tools(request):
    return render(request, "controls/specialized_tools.html")


# -------------------------------------------------------------------
# Category & Set Price maintenance
# -------------------------------------------------------------------
@login_required
def add_category(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            # Tell HTMX lists to refresh
            return HttpResponse(status=204, headers={"HX-Trigger": "CategoryListChanged"})
    return render(request, "pricesheet/modals/add_category.html", {"form": form})


@login_required
def add_subcategory(request):
    form = SubCategoryForm(request.POST or None)
    categories = Category.objects.filter(active__in=[True, 1, None]).order_by("name")

    if request.method == "POST" and form.is_valid():
        obj = form.save()
        if obj.category and getattr(obj.category, "setprice", False):
            SetPriceCategory.objects.get_or_create(category=obj.category, name=obj.name)
        # 204 No Content (tests assert 204)
        return HttpResponse(status=204)

    return render(request, "controls/add_subcategory.html", {"form": form, "categories": categories})


@login_required
def add_setprice_category(request):
    form = AddSetPriceCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.updated = timezone.now()
        obj.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "CategoryAdded"})
    return render(request, "pricesheet/modals/add_setprice_category.html", {"form": form})


@login_required
def add_setprice_item(request):
    form = AddSetPriceItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.updated = timezone.now()
        obj.save()
        return HttpResponse(
            status=204, headers={"HX-Trigger": "TemplateListChanged", "category": "3"}
        )
    return render(request, "pricesheet/modals/add_setprice_item.html", {"form": form})


# -------------------------------------------------------------------
# Bulk workorder maintenance
# -------------------------------------------------------------------
@login_required
def mark_all_verified(request):
    Workorder.objects.filter(completed=1).update(checked_and_verified=1)
    messages.success(request, "All completed workorders marked verified.")
    return render(request, "controls/utilities.html")


@login_required
def mark_all_invoiced(request):
    Workorder.objects.exclude(billed=0).filter(completed=1).update(invoice_sent=1)
    messages.success(request, "All billed workorders marked invoice_sent=1.")
    return render(request, "controls/utilities.html")


@login_required
def missing_workorders(request):
    """
    Given a numeric range and a company selector, compute workorder numbers
    that are missing compared to what's stored.
    """
    if request.method == "POST":
        start_s = request.POST.get("start")
        end_s = request.POST.get("end")
        company_s = request.POST.get("company")

        try:
            start = int(start_s)
            end = int(end_s)
            company = int(company_s)
        except (TypeError, ValueError):
            return render(request, "controls/missing_workorders.html")

        # Determine which field to check by company
        # 1 = Printleader, 2 = LK, 3 = KOS   (based on your prior code)
        if company == 1:
            existing_qs = Workorder.objects.exclude(printleader_workorder__isnull=True).values_list(
                "printleader_workorder", flat=True
            )
        elif company == 2:
            existing_qs = Workorder.objects.exclude(lk_workorder__isnull=True).values_list(
                "lk_workorder", flat=True
            )
        elif company == 3:
            existing_qs = Workorder.objects.exclude(kos_workorder__isnull=True).values_list(
                "printleader_workorder", flat=True
            )
        else:
            return render(request, "controls/missing_workorders.html")

        # Clean to integers (digits only)
        existing = []
        for v in existing_qs:
            try:
                if isinstance(v, int):
                    existing.append(v)
                else:
                    v_str = str(v).strip()
                    if v_str.isdigit():
                        existing.append(int(v_str))
            except Exception:
                # skip malformed values
                pass

        desired = set(range(start, end + 1))
        missing = sorted(desired - set(existing))

        return render(request, "controls/missing_workorders.html", {"missing": missing})

    return render(request, "controls/missing_workorders.html")


@login_required
def update_complete_date(request):
    Workorder.objects.filter(completed=1).update(date_completed=F("updated"))
    messages.success(request, "Updated date_completed from updated for completed workorders.")
    return render(request, "controls/utilities.html")


# -------------------------------------------------------------------
# Customer/ShipTo backfill helpers
# -------------------------------------------------------------------
@login_required
def customer_shipto(request):
    for c in Customer.objects.all():
        ShipTo.objects.create(
            customer_id=c.pk,
            company_name=c.company_name,
            first_name=c.first_name,
            last_name=c.last_name,
            address1=c.address1,
            address2=c.address2,
            city=c.city,
            state=c.state,
            zipcode=c.zipcode,
            phone1=c.phone1,
            phone2=c.phone2,
            email=c.email,
            website=c.website,
            logo=c.logo,
            notes=c.notes,
            active=c.active,
        )
    messages.success(request, "Created ShipTo rows for all customers.")
    return render(request, "controls/utilities.html")


@login_required
def workorder_ship(request):
    for wo in Workorder.objects.all():
        try:
            shipto = ShipTo.objects.get(customer_id=wo.customer_id)
            Workorder.objects.filter(pk=wo.pk).update(ship_to_id=shipto.pk)
        except ShipTo.DoesNotExist:
            pass
    messages.success(request, "Linked Workorders to ShipTo where available.")
    return render(request, "controls/utilities.html")


# -------------------------------------------------------------------
# Inventory helpers (using InventoryMaster model methods)
# -------------------------------------------------------------------
@login_required
def create_inventory_from_inventory(request):
    for inv in Inventory.objects.all():
        if not inv.internal_part_number:
            item = InventoryMaster.objects.create(
                name=inv.name,
                description=inv.description,
                supplies=True,
                retail=True,
                primary_vendor_part_number=inv.vendor_part_number,
                primary_base_unit=inv.measurement,
                unit_cost=inv.unit_cost or 0,
                price_per_m=inv.price_per_m,
            )
            Inventory.objects.filter(pk=inv.pk).update(internal_part_number=item.pk)
    messages.success(request, "Created InventoryMaster rows for inventory without IPN.")
    return render(request, "controls/specialized_tools.html")


@login_required
def add_primary_vendor(request):
    if request.method == "POST":
        vendor_id = request.POST.get("vendor")
        id_list = request.POST.getlist("item")
        for pk in id_list:
            try:
                item = InventoryMaster.objects.get(pk=pk)
                item.set_primary_vendor(vendor_id)
            except InventoryMaster.DoesNotExist:
                continue
        messages.success(request, "Primary vendor set for selected items.")
        return redirect("controls:view_price_groups")

    items = InventoryMaster.objects.all()
    vendors = Vendor.objects.order_by("name")
    return render(request, "controls/add_primary_vendor.html", {"items": items, "vendors": vendors})


@login_required
def add_primary_baseunit(request):
    items = InventoryMaster.objects.all()
    if request.method == "POST":
        unit_id = request.POST.get("unit")
        qty = request.POST.get("qty")
        id_list = request.POST.getlist("item")
        try:
            qty_val = int(qty)
        except (TypeError, ValueError):
            qty_val = None
        for pk in id_list:
            try:
                item = InventoryMaster.objects.get(pk=pk)
            except InventoryMaster.DoesNotExist:
                continue
            if unit_id and qty_val is not None:
                item.set_primary_base_unit(unit_id, qty_val)
        messages.success(request, "Primary base unit updated.")
        # Render with 200, not a redirect
        return render(request, "controls/add_primary_baseunit.html",
                      {"items": items}, status=200)
    return render(request, "controls/add_primary_baseunit.html", {"items": items})


@login_required
def add_units_per_base_unit(request):
    items = InventoryMaster.objects.all()

    if request.method == "POST":
        qty_raw = request.POST.get("qty")
        id_list = request.POST.getlist("item") or []

        # Parse qty
        try:
            qty_val = int(qty_raw)
        except (TypeError, ValueError):
            qty_val = None

        updated_ids = []
        if qty_val is not None:
            for pk in id_list:
                item = InventoryMaster.objects.filter(pk=pk).first()
                if not item:
                    continue
                item.set_units_per_base_unit(qty_val)
                updated_ids.append(pk)
            messages.success(request, "Units per base unit updated for selected items.")
        else:
            messages.error(request, "Please enter a valid quantity.")

        context = {
            "items": items,
            "updated_ids": updated_ids,
            "qty": qty_raw,
        }
        return render(request, "controls/add_units_per_base_unit.html", context, status=200)

    # GET
    return render(request, "controls/add_units_per_base_unit.html", {"items": items})


# -------------------------------------------------------------------
# Price groups
# -------------------------------------------------------------------
def view_price_groups(request):
    groups = GroupCategory.objects.order_by("name")
    return render(request, "controls/view_price_groups.html", {"group": groups})


def view_price_group_detail(request, id=None):
    group = get_object_or_404(GroupCategory, pk=id)
    through_rows = InventoryPricingGroup.objects.filter(group=id)
    return render(
        request,
        "controls/view_price_group_detail.html",
        {"group_id": group, "group": through_rows},
    )


def add_price_group(request):
    if request.method == "POST":
        group_name = request.POST.get("group_name")
        if group_name:
            GroupCategory.objects.create(name=group_name)
            messages.success(request, f"Group '{group_name}' created.")
            return redirect("controls:view_price_groups")
    return render(request, "controls/add_price_group.html")


def add_price_group_item(request, id=None, which=None):
    """
    GET variants:
        /controls/add_price_group_item/<id>/
        /controls/add_price_group_item/<id>/all
        /controls/add_price_group_item/<id>/nogroup
        /controls/add_price_group_item/<id>/group
    POST:
        - with 'notgrouped' flag -> mark items as not_grouped
        - else add items to group via InventoryMaster.add_to_price_group()
    """
    group_id = id
    groups = GroupCategory.objects.order_by("name")

    items = InventoryMaster.objects.all()
    if which == "nogroup":
        items = items.filter(not_grouped=1)
    elif which == "group":
        items = items.filter(grouped=1)

    if request.method == "POST":
        notgrouped = request.POST.get("notgrouped")
        group_id = request.POST.get("group_id") or group_id
        id_list = request.POST.getlist("item")

        if not id_list:
            messages.info(request, "No items selected.")
            return redirect("controls:view_price_groups")

        if notgrouped:
            InventoryMaster.objects.filter(pk__in=id_list).update(not_grouped=1)
            messages.success(request, "Marked selected items as Not Grouped.")
            return redirect("controls:view_price_groups")

        # validate group if provided
        if group_id:
            get_object_or_404(GroupCategory, pk=group_id)

        # add to group
        for pk in id_list:
            try:
                item = InventoryMaster.objects.get(pk=pk)
            except InventoryMaster.DoesNotExist:
                continue
            if group_id:
                # requires InventoryMaster.add_to_price_group/add_to_group to use InventoryPricingGroup(inventory=...)
                item.add_to_price_group(group_id)

        messages.success(request, "Added selected items to the group.")
        return redirect("controls:view_price_group_detail", id=group_id)

    context = {"group_id": group_id, "items": items, "groups": groups}
    if which == "all":
        return render(request, "controls/partials/price_group_all.html", context)
    if which == "nogroup":
        return render(request, "controls/partials/price_group_notgrouped.html", context)
    if which == "group":
        return render(request, "controls/partials/price_group_grouped.html", context)
    return render(request, "controls/add_price_group_item.html", context)


def add_item_variation(request):
    units = Measurement.objects.all()
    return render(request, "controls/partials/add_item_variation.html", {"units": units})


@login_required
def add_base_qty_variation(request):
    """
    Ensure each item with primary_base_unit & units_per_base_unit has a matching
    InventoryQtyVariations row.
    """
    for item in InventoryMaster.objects.all():
        if item.primary_base_unit and item.units_per_base_unit:
            InventoryQtyVariations.objects.get_or_create(
                inventory=item,
                variation=item.primary_base_unit,
                defaults={"variation_qty": item.units_per_base_unit},
            )
    messages.success(request, "Base quantity variations created where missing.")
    return redirect("controls:utilities")


def add_internal_part_number(request):
    # Placeholder route
    return render(request, "controls/utilities.html")


# -------------------------------------------------------------------
# Reporting helpers
# -------------------------------------------------------------------
def get_highest_item_price(request):
    """
    Example utility: recompute & store the high price for a specific item.
    """
    item = get_object_or_404(InventoryMaster, pk=201)
    item.update_high_price_from_invoices()
    messages.success(request, f"Updated high price for {item.name}.")
    return render(request, "controls/utilities.html")


def items_missing_details(request):
    items = VendorItemDetail.objects.all()
    return render(request, "controls/items_missing_details.html", {"items": items})


def high_price_item(request):
    """
    Recompute the highest unit_cost from InvoiceItem for all inventory (excluding non-inventory)
    and store into InventoryMaster.high_price
    """
    for item in InventoryMaster.objects.exclude(non_inventory=1):
        item.update_high_price_from_invoices()
    messages.success(request, "High price recomputed for all inventory items.")
    return render(request, "controls/utilities.html")

@login_required
def cust_history(request):
    customers = Workorder.objects.all().order_by("hr_customer")
    unique_list = []
    seen = set()
    for wo in customers:
        if wo.hr_customer not in seen:
            unique_list.append(wo)
            seen.add(wo.hr_customer)
    context = {"unique_list": unique_list, "customer": customers}
    return render(request, "controls/workorder_history.html", context)

@login_required
def cust_address(request):
    customers = Workorder.objects.all().order_by("hr_customer")
    unique_list = []
    seen = set()
    for wo in customers:
        if wo.hr_customer not in seen:
            unique_list.append(wo)
            seen.add(wo.hr_customer)
    return render(request, "controls/customers_with_address.html", {"unique_list": unique_list})

@login_required
def cust_wo_address(request):
    customers = Workorder.objects.all().order_by("hr_customer")
    unique_list = []
    seen = set()
    for wo in customers:
        if wo.hr_customer not in seen:
            unique_list.append(wo)
            seen.add(wo.hr_customer)
    return render(request, "controls/customers_without_address.html", {"unique_list": unique_list})


# -------------------------------------------------------------------
# A/R statements for Krueger
# -------------------------------------------------------------------
@login_required
def krueger_statements(request):
    today = timezone.now()
    customers = Customer.objects.order_by("company_name")
    workorders = (
        Workorder.objects.exclude(billed=0)
        .exclude(internal_company="LK Design")
        .exclude(paid_in_full=1)
        .exclude(quote=1)
        .exclude(void=1)
    )
    statement = Krueger_Araging.objects.filter(
        hr_customer__in=workorders.values_list("hr_customer", flat=True).distinct()
    ).order_by("hr_customer")

    total_balance = workorders.aggregate(Sum("open_balance"))

    ar = Krueger_Araging.objects.all().order_by("hr_customer")
    totals = {
        "total_current": ar.aggregate(Sum("current")),
        "total_thirty": ar.aggregate(Sum("thirty")),
        "total_sixty": ar.aggregate(Sum("sixty")),
        "total_ninety": ar.aggregate(Sum("ninety")),
        "total_onetwenty": ar.aggregate(Sum("onetwenty")),
    }

    context = {
        **totals,
        "total_balance": total_balance,
        "ar": ar,
        "workorders": workorders,
        "statement": statement,
    }
    return render(request, "finance/reports/krueger_statements.html", context)


@login_required
def krueger_ar_aging(request):
    today = timezone.now()
    customers = Customer.objects.order_by("company_name")
    workorders = (
        Workorder.objects.exclude(billed=0)
        .exclude(paid_in_full=1)
        .exclude(quote=1)
        .exclude(void=1)
        .exclude(internal_company="LK Design")
    )

    # Update age in days for each relevant workorder
    for wo in workorders:
        date_billed = wo.date_billed or today
        age_days = abs((date_billed - today).days)
        Workorder.objects.filter(pk=wo.pk).update(aging=age_days)

    # Aggregate aging buckets per customer
    for cust in customers:
        if not Workorder.objects.filter(customer_id=cust.id).exists():
            continue

        qs = workorders.filter(customer_id=cust.id)

        def sum_balance(q):
            val = q.aggregate(Sum("open_balance"))
            return list(val.values())[0] or 0

        current = sum_balance(qs.exclude(aging__gt=29))
        thirty = sum_balance(qs.exclude(aging__lt=30).exclude(aging__gt=59))
        sixty = sum_balance(qs.exclude(aging__lt=60).exclude(aging__gt=89))
        ninety = sum_balance(qs.exclude(aging__lt=90).exclude(aging__gt=119))
        onetwenty = sum_balance(qs.exclude(aging__lt=120))
        total = sum_balance(qs)

        try:
            Krueger_Araging.objects.filter(customer_id=cust.id).update(
                hr_customer=cust.company_name,
                date=today,
                current=current,
                thirty=thirty,
                sixty=sixty,
                ninety=ninety,
                onetwenty=onetwenty,
                total=total,
            )
        except Krueger_Araging.DoesNotExist:
            Krueger_Araging.objects.create(
                customer_id=cust.id,
                hr_customer=cust.company_name,
                date=today,
                current=current,
                thirty=thirty,
                sixty=sixty,
                ninety=ninety,
                onetwenty=onetwenty,
                total=total,
            )

    ar = Krueger_Araging.objects.all().order_by("hr_customer")
    context = {
        "total_current": ar.aggregate(Sum("current")),
        "total_thirty": ar.aggregate(Sum("thirty")),
        "total_sixty": ar.aggregate(Sum("sixty")),
        "total_ninety": ar.aggregate(Sum("ninety")),
        "total_onetwenty": ar.aggregate(Sum("onetwenty")),
        "total_balance": workorders.aggregate(Sum("open_balance")),
        "ar": ar,
    }
    return render(request, "finance/reports/krueger_statements.html", context)

@login_required
def add_to_item_list(request):
    """
    Legacy placeholder to keep the existing URL working.
    Replace with real logic or remove the route if unused.
    """
    return HttpResponse("add_to_item_list is not implemented.", status=200)
