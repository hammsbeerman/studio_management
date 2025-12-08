from decimal import Decimal, InvalidOperation
import json
from datetime import timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q, Count, Sum, F, ExpressionWrapper, DecimalField, Max, OuterRef, Subquery, IntegerField, Value
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRefresh
from django.db import transaction
from django.core.paginator import Paginator
from inventory.services.pricing import (
    compute_retail_price, 
    get_effective_retail_price,
    ensure_retail_pricing,
)
from inventory.services.ledger import (
    get_on_hand, 
    record_inventory_movement,
    get_qty_sold_summary,
    get_stock_alerts,
)
from retail.delivery_utils import (
    get_sticky_delivery_date,
    set_sticky_delivery_date,
    ensure_sale_delivery,
    sync_workorder_delivery_from_sale,
    ensure_route_entry_for_customer,
)
from controls.models import Numbering, RetailInventoryCategory, RetailInventorySubCategory  # if still used elsewhere


from inventory.models import (
    Vendor, 
    InventoryMaster, 
    RetailWorkorderItem, 
    Inventory, 
    InventoryLedger,
    InventoryQtyVariations,
)
from .models import RetailSale, RetailSaleLine, RetailCashSale, RetailPayment, Delivery, DeliveryRouteEntry
from .forms import PaymentMethodForm, RefundLookupForm
from customers.models import Customer, ShipTo
from workorders.models import Workorder, JobStatus
from workorders.views import _next_number_by_name
from workorders.utils import apply_pos_adjustment_to_workorder
from workorders.services.totals import compute_workorder_totals

STATUS_PENDING = "PENDING"
STATUS_CANCELLED = "CANCELLED"



# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

# def _get_sticky_delivery_date(request):
#     """
#     Read last used delivery date from session or default to today.
#     """
#     last_date_str = request.session.get("last_delivery_date")
#     if last_date_str:
#         try:
#             return datetime.strptime(last_date_str, "%Y-%m-%d").date()
#         except Exception:
#             pass
#     return timezone.localdate()


# def _set_sticky_delivery_date(request, date_obj):
#     """
#     Save last used delivery date in session.
#     """
#     request.session["last_delivery_date"] = date_obj.strftime("%Y-%m-%d")

# def ensure_route_entry_for_customer(customer: Customer) -> DeliveryRouteEntry:
#     entry, created = DeliveryRouteEntry.objects.get_or_create(customer=customer)
#     if created:
#         max_order = DeliveryRouteEntry.objects.aggregate(m=Max("sort_order"))["m"] or 0
#         entry.sort_order = max_order + 10
#         entry.save()
#     return entry

# def _ensure_sale_delivery(sale, scheduled_date):
#     """
#     Ensure there is a PENDING Delivery for a sale at given date.
#     """
#     delivery, created = Delivery.objects.get_or_create(
#         sale=sale,
#         defaults={
#             "customer": sale.customer,
#             "scheduled_date": scheduled_date,
#             "status": STATUS_PENDING,
#         },
#     )
#     if not created:
#         delivery.scheduled_date = scheduled_date
#         delivery.status = STATUS_PENDING
#         delivery.save()
#     return delivery


# def _sync_workorder_delivery_from_sale(sale, scheduled_date=None):
#     """
#     Keep Workorder delivery flags in sync with sale.requires_delivery.
#     Optionally update workorder.delivery_date when scheduled_date given.
#     """
#     wo = getattr(sale, "workorder", None)
#     if not wo:
#         return

#     wo.requires_delivery = sale.requires_delivery
#     if sale.requires_delivery and scheduled_date is not None:
#         wo.delivery_date = scheduled_date
#     elif not sale.requires_delivery:
#         wo.delivery_date = None

#     wo.save()

def _get_sorted_deliveries_for_date(selected_date):
    """
    Return deliveries for the given date, ordered by the customer's
    DeliveryRouteEntry.sort_order, then customer name.
    """

    route_qs = DeliveryRouteEntry.objects.filter(
        customer=OuterRef("customer")
    ).values("sort_order")[:1]

    qs = (
        Delivery.objects
        .select_related("customer", "sale", "workorder")
        .filter(
            scheduled_date=selected_date,
            status=STATUS_PENDING,
        )
        .annotate(
            route_sort_raw=Subquery(route_qs, output_field=IntegerField()),
            route_sort=Coalesce(
                "route_sort_raw",
                Value(999999, output_field=IntegerField()),  # no entry → bottom
            ),
        )
        .order_by("route_sort", "customer__company_name", "pk")
    )

    return qs

def _record_pos_ledger_entries(sale: RetailSale, scale: Decimal = Decimal("1.0")):
    """
    Write InventoryLedger entries for this POS sale / refund.

    - For normal sales (qty > 0), we subtract stock (negative delta).
    - For refunds (qty < 0 on refund sale), we add stock back (positive delta).
    - For partial refunds, `scale` lets us only move a fraction of that qty.
    """
    source_type = "POS_REFUND" if sale.is_refund else "POS_SALE"

    for line in sale.lines.filter(inventory__isnull=False):
        qty = line.qty or Decimal("0")
        try:
            qty_dec = Decimal(qty)
        except Exception:
            continue

        if qty_dec == 0:
            continue

        # Sale:   qty=+3  -> delta=-3 (stock out)
        # Refund: qty=-3  -> delta=+3 (restock)
        # Partial refund: scale < 1.0, so we only restock part of it.
        qty_delta = (-qty_dec) * scale

        record_inventory_movement(
            inventory_item=line.inventory,
            qty_delta=qty_delta,
            source_type=source_type,
            source_id=str(sale.id),
            note=f"POS {'refund' if sale.is_refund else 'sale'} #{sale.id}",
        )

def _compute_sale_totals(sale: RetailSale):
    """
    Compute subtotal, tax, and total for a RetailSale based on its lines and tax flags.
    """
    subtotal = Decimal("0.00")

    for line in sale.lines.all():
        qty = line.qty or 0
        unit_price = line.unit_price or 0

        try:
            qty_dec = Decimal(qty)
        except Exception:
            qty_dec = Decimal("0")

        try:
            unit_price_dec = Decimal(unit_price)
        except Exception:
            unit_price_dec = Decimal("0")

        subtotal += (qty_dec * unit_price_dec)

    subtotal = subtotal.quantize(Decimal("0.01"))

    if sale.tax_exempt or not sale.tax_rate:
        tax = Decimal("0.00")
    else:
        tax = (subtotal * sale.tax_rate).quantize(Decimal("0.01"))

    total = subtotal + tax
    return subtotal, tax, total


def _is_walkin_customer(cust: Customer) -> bool:
    """
    Identify the special Walk-in / Cash customer.
    """
    if not cust:
        return False
    return (
        getattr(cust, "customer_number", "") == "WALKIN"
        or getattr(cust, "company_name", "") == "Walk-in / Cash Sale"
    )


def _sync_sale_lines_to_workorder(sale, workorder):
    """
    Copy all RetailSale lines onto the workorder as RetailWorkorderItem rows.

    - First delete any existing POS rows for (workorder, sale) so we don't duplicate.
    - If the sale has no POS lines, we just clear existing POS rows and recompute
      workorder totals so POS no longer contributes.
    """

    # 1) Clear old POS items for this combo
    RetailWorkorderItem.objects.filter(workorder=workorder, sale=sale).delete()

    # 2) Get sale lines (supporting either related_name="lines" or default rel)
    lines_qs = getattr(sale, "lines", None) or sale.retailsaleline_set
    lines = list(lines_qs.all())

    # 3) If no lines left on the sale, just recompute totals and return
    if not lines:
        totals = compute_workorder_totals(workorder)
        workorder.subtotal = f"{totals.subtotal:.2f}"
        workorder.tax = f"{totals.tax:.2f}"
        workorder.workorder_total = f"{totals.total:.2f}"
        workorder.total_balance = totals.total
        workorder.open_balance = totals.total
        workorder.save(
            update_fields=[
                "subtotal",
                "tax",
                "workorder_total",
                "total_balance",
                "open_balance",
            ]
        )
        return

    # 4) Recreate POS items from sale lines
    for line in lines:
        qty = Decimal(line.qty or 0)
        unit_price = Decimal(line.unit_price or 0)

        # Prefer stored line_total if present; fall back to qty * unit_price
        line_total = getattr(line, "line_total", None)
        if line_total is None:
            line_total = qty * unit_price

        RetailWorkorderItem.objects.create(
            workorder=workorder,
            sale=sale,
            customer=sale.customer,
            inventory=getattr(line, "inventory", None),
            description=(getattr(line, "description", "") or "").strip(),
            quantity=qty,
            unit_price=unit_price,
            total_price=line_total,
        )

    # 5) Recompute unified totals (regular + POS) after sync
    totals = compute_workorder_totals(workorder)
    workorder.subtotal = f"{totals.subtotal:.2f}"
    workorder.tax = f"{totals.tax:.2f}"
    workorder.workorder_total = f"{totals.total:.2f}"
    workorder.total_balance = totals.total
    workorder.open_balance = totals.total
    workorder.save(
        update_fields=[
            "subtotal",
            "tax",
            "workorder_total",
            "total_balance",
            "open_balance",
        ]
    )


def _ensure_sale_workorder(sale, as_quote: bool = False):
    """
    Ensure there is a Workorder (or Quote) for this sale.

    - Walk-in customers: return None.
    - If sale.workorder exists: just return it (we won't auto-convert modes here).
    - If no workorder yet:
        * as_quote=True  → create a Quote using Quote Number
        * as_quote=False → create a normal Workorder using Workorder Number
    """
    cust = sale.customer
    if cust is None:
        return None

    if _is_walkin_customer(cust):
        return None
    
    # 🔹 NEW: don’t create a workorder if there are no lines at all
    if not sale.lines.exists():
        raise ValueError("Cannot create a workorder for a sale with no line items.")

    # If already linked, don't create another
    existing = getattr(sale, "workorder", None)
    if existing:
        return existing

    # ShipTo — reuse first or clone from customer
    shipto = ShipTo.objects.filter(customer=cust).first()
    if not shipto:
        shipto = ShipTo.objects.create(
            customer=cust,
            company_name=cust.company_name,
            first_name=getattr(cust, "first_name", "") or "",
            last_name=getattr(cust, "last_name", "") or "",
            address1=cust.address1,
            address2=cust.address2,
            city=cust.city,
            state=cust.state,
            zipcode=cust.zipcode,
            phone1=cust.phone1,
            phone2=cust.phone2,
            email=cust.email,
            website=cust.website,
            notes=getattr(cust, "notes", ""),
            active=cust.active,
        )

    # Decide numbering + status based on quote vs workorder
    if as_quote:
        num = _next_number_by_name("Quote Number")  # 🔹 same as Krueger / LK
        quote_flag = "1"
        quote_number = str(num)
        workorder_number = str(num)  # quotes use quote number in workorder field
        status_name = "Quoted"
    else:
        num = _next_number_by_name("Workorder Number")
        quote_flag = "0"
        quote_number = None
        workorder_number = str(num)
        status_name = "Open"

    # Resolve / create JobStatus by name
    status = JobStatus.objects.filter(name__iexact=status_name).first()
    if not status:
        status = JobStatus.objects.create(name=status_name)

    # Tax flag: sale override wins, else customer
    tax_exempt = bool(getattr(sale, "tax_exempt", False) or getattr(cust, "tax_exempt", False))

    hr_customer = cust.company_name or (
        f"{getattr(cust, 'first_name', '')} {getattr(cust, 'last_name', '')}".strip() or None
    )

    wo = Workorder.objects.create(
        customer=cust,
        ship_to=shipto,
        hr_customer=hr_customer,
        workorder=workorder_number,
        internal_company="Office Supplies",
        quote=quote_flag,
        quote_number=quote_number,
        workorder_status=status,
        tax_exempt=tax_exempt,
        po_number=getattr(cust, "po_number", None),
        description=(sale.notes or ""),
    )

    sale.workorder = wo
    sale.save(update_fields=["workorder"])

    return wo

def _guard_sale_unlocked(sale: RetailSale):
    """
    Raise if this POS sale has been locked (paid/completed).
    Use in any view that mutates lines, customer, or notes.
    """
    if sale.locked:
        raise PermissionDenied("This sale is locked and cannot be edited.")

def _ensure_pos_number(sale):
    """
    Ensure sale.pos_number is set if the field exists on the model.
    Safe to call even if the field does not exist (old schema).
    """    
    # Old schema: no `pos_number` field at all
    if not hasattr(sale, "pos_number"):
        return

    # Already has a POS number
    if sale.pos_number:
        return

    # Simple default: use the sale ID as the POS number
    sale.pos_number = str(sale.id)
    sale.save(update_fields=["pos_number"])


# --------------------------------------------------------------------------------------
# Basic totals + inventory views
# --------------------------------------------------------------------------------------

@login_required
def sale_totals(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    subtotal, tax, total = _compute_sale_totals(sale)
    ctx = {
        "sale": sale,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }
    return render(request, "retail/partials/totals.html", ctx)


@login_required
def retail_inventory_list(request):
    items = InventoryMaster.objects.all()
    context = {
        "items": items,
    }
    return render(request, "retail/inventory/inventory_list.html", context)


# --------------------------------------------------------------------------------------
# POS main flow
# --------------------------------------------------------------------------------------

@login_required
def retail_new_sale(request):
    """
    Start a new POS sale.

    Reuse an existing blank open sale for this cashier
    (no customer, no lines, no payments, not a refund),
    otherwise create a new one.
    """
    sale = (
        RetailSale.objects
        .filter(
            cashier=request.user,
            status=RetailSale.STATUS_OPEN,  # or "open" if you're using strings
            locked=False,
            is_refund=False,
            customer__isnull=True,
        )
        .annotate(
            line_count=Count("lines"),
            payment_count=Count("payments"),
        )
        .filter(
            line_count=0,
            payment_count=0,
        )
        .filter(
            Q(notes__isnull=True) | Q(notes="")  # 👈 allow NULL or empty
        )

        .first()
    )

    if not sale:
        sale = RetailSale.objects.create(
            cashier=request.user,
            internal_company="Office Supplies",
            status=RetailSale.STATUS_OPEN,
            locked=False,
            # NOTE: do NOT assign pos_number here
        )

    return redirect("retail:sale_detail", pk=sale.pk)


@login_required
def retail_sale_detail(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    customers = Customer.objects.filter(active=True).order_by("company_name")

    open_invoices = closed_invoices = None
    if sale.customer:
        base_qs = (
            Workorder.objects.filter(
                customer=sale.customer,
                quote="0",
                internal_company__in=["Krueger Printing", "Office Supplies"],
            )
            .order_by("-date_billed", "-id")
        )
        open_invoices = base_qs.filter(open_balance__gt=0)
        closed_invoices = base_qs.exclude(open_balance__gt=0)

    return render(
        request,
        "retail/sale_detail.html",
        {
            "sale": sale,
            "customers": customers,
            "open_invoices": open_invoices,
            "closed_invoices": closed_invoices,
            "is_walkin": _is_walkin_customer(sale.customer),
        },
    )


@login_required
def inventory_search(request):
    q = request.GET.get("q", "").strip()

    results = InventoryMaster.objects.none()
    if q:
        results = (
            InventoryMaster.objects.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(primary_vendor_part_number__icontains=q)
                # 🔹 also match vendor part numbers from Inventory
                | Q(inventory__vendor_part_number__icontains=q)
            )
            .filter(active=True)
            .distinct()
            .order_by("name")[:50]
        )

    # 🔹 attach on_hand to each result so the template doesn't have to call anything
    for item in results:
        item.on_hand = get_on_hand(item)

    sale_id = request.GET.get("sale_id")
    sale = None
    if sale_id:
        try:
            sale = RetailSale.objects.get(pk=int(sale_id))
        except (RetailSale.DoesNotExist, ValueError):
            sale = None

    return render(
        request,
        "retail/partials/inventory_search_results.html",
        {"results": results, "sale": sale},
    )

@login_required
def inventory_item_modal(request, pk):
    """
    HTMX modal content: show inventory item details + pricing breakdown
    for a POS line item, plus all Inventory rows tied to this master.
    """
    item = get_object_or_404(InventoryMaster, pk=pk)

    # Pricing snapshot (don’t reset override here)
    pricing = ensure_retail_pricing(item, reset_override=False)
    effective_price = get_effective_retail_price(item)

    # All stock entries for this master item
    inventories = (
        Inventory.objects.filter(internal_part_number=item)
        .order_by("-created")
    )

    # NEW: on-hand using ledger with legacy fallback
    on_hand = get_on_hand(item)

    context = {
        "item": item,
        "pricing": pricing,
        "effective_price": effective_price,
        "inventories": inventories,
        "on_hand": on_hand,
    }
    return render(request, "retail/partials/inventory_item_modal.html", context)


@require_POST
@login_required
def add_line_from_inventory(request, pk, inventory_id):
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)
    item = get_object_or_404(InventoryMaster, pk=inventory_id)

    # Qty from modal (string -> Decimal)
    qty_str = (request.POST.get("qty") or "1").strip()
    try:
        qty = Decimal(qty_str)
    except Exception:
        qty = Decimal("1")

    # Optional sold_variation from modal
    variation_id = (request.POST.get("variation_id") or "").strip()
    sold_variation = None
    if variation_id:
        try:
            sold_variation = InventoryQtyVariations.objects.get(pk=variation_id, inventory=item)
        except InventoryQtyVariations.DoesNotExist:
            sold_variation = None

    # NEW: default price comes from InventoryRetailPrice (override → calc → purchase)
    unit_price = get_effective_retail_price(item)

    # 🔹 If exactly one variation exists, use it as the default
    variations = InventoryQtyVariations.objects.filter(inventory=item)
    sold_variation = variations.first() if variations.count() == 1 else None

    line = RetailSaleLine.objects.create(
        sale=sale,
        inventory=item,
        description=item.name,
        qty=qty,
        unit_price=unit_price,
        tax_rate=Decimal("0.00"),  # pos tax handled at sale level
        sold_variation=sold_variation
    )

    # row number for "#" column – count after create
    rownum = sale.lines.count()

    response = render(
        request,
        "retail/partials/line_row.html",
        {
            "sale": sale,
            "line": line,
            "rownum": rownum,
        },
    )
    response["HX-Trigger"] = "retail-totals-changed"
    return response


@require_POST
@login_required
def update_line_field(request, line_id):
    line = get_object_or_404(RetailSaleLine, pk=line_id)
    sale = line.sale
    _guard_sale_unlocked(sale)

    field = request.POST.get("field")
    value = request.POST.get("value")

    if field not in {"qty", "unit_price", "tax_rate"}:
        return HttpResponseBadRequest("Invalid field")

    try:
        if field == "qty":
            line.qty = Decimal(value or "0")
        elif field == "unit_price":
            line.unit_price = Decimal(value or "0")
        elif field == "tax_rate":
            line.tax_rate = Decimal(value or "0")
    except Exception:
        return HttpResponseBadRequest("Invalid value")

    line.save()

    response = render(
        request,
        "retail/partials/line_row.html",
        {"line": line},
    )
    response["HX-Trigger"] = "retail-totals-changed"
    return response


@require_POST
@login_required
def delete_line(request, line_id):
    line = get_object_or_404(RetailSaleLine, pk=line_id)
    sale = line.sale
    _guard_sale_unlocked(sale)
    line.delete()
    return HttpResponseClientRefresh()


@require_POST
@login_required
def set_sale_customer(request, pk):
    """
    Set / change the customer on the POS sale and update tax flags.
    Walk-in/cash uses a dedicated WALKIN customer record.
    """
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    customer_id = request.POST.get("customer_id") or None
    if not customer_id:
        # Dedicated Walk-in customer record for history/filters
        walkin, created = Customer.objects.get_or_create(
            customer_number="WALKIN",
            defaults={
                "company_name": "Walk-in / Cash Sale",
                "first_name": "Walk-in",
                "last_name": "Customer",
                "address1": "",
                "address2": "",
                "city": "",
                "state": "",
                "zipcode": "",
                "phone1": "",
                "phone2": "",
                "email": "",
                "website": "",
                "po_number": "",
                "avg_days_to_pay": "",
            },
        )
        sale.customer = walkin
        sale.tax_exempt = False
        sale.tax_rate = Decimal("0.055")
        sale.save(update_fields=["customer", "tax_exempt", "tax_rate"])

        customer_html = render_to_string(
            "retail/partials/customer_info_block.html",
            {"sale": sale, "customer": walkin},
            request=request,
        )
    else:
        customer = get_object_or_404(Customer, pk=customer_id)
        sale.customer = customer

        # tie POS tax status to customer
        is_exempt = bool(getattr(customer, "tax_exempt", False))
        sale.tax_exempt = is_exempt
        sale.tax_rate = Decimal("0.000") if sale.tax_exempt else Decimal("0.055")

        sale.save(update_fields=["customer", "tax_exempt", "tax_rate"])

        customer_html = render_to_string(
            "retail/partials/customer_info_block.html",
            {"sale": sale, "customer": customer},
            request=request,
        )

    # 👇 NEW: render delivery toggle based on updated sale + walkin flag
    delivery_html = render_to_string(
        "retail/partials/sale_delivery_toggle.html",
        {
            "sale": sale,
            "is_walkin": _is_walkin_customer(sale.customer),
        },
        request=request,
    )

    # main target = customer block; delivery updated OOB
    full_html = (
        customer_html
        + f'<div id="delivery-toggle" hx-swap-oob="true">{delivery_html}</div>'
    )

    resp = HttpResponse(full_html)
    resp["HX-Trigger"] = json.dumps({
        "retail-totals-changed": True,
        "customer-changed": True,
    })
    return resp


@login_required
def retail_sale_customer_ar(request, pk):
    """
    Render the Customer AR panel for the POS, showing all Krueger + Office Supplies
    invoices for the selected customer.
    """
    sale = get_object_or_404(RetailSale, pk=pk)
    open_invoices = closed_invoices = None
    if sale.customer:
        base_qs = (
            Workorder.objects.filter(
                customer=sale.customer,
                quote="0",
                internal_company__in=["Krueger Printing", "Office Supplies"],
            )
            .order_by("-date_billed", "-id")
        )
        open_invoices = base_qs.filter(open_balance__gt=0)
        closed_invoices = base_qs.exclude(open_balance__gt=0)

    return render(
        request,
        "retail/partials/customer_ar_panel.html",
        {
            "sale": sale,
            "open_invoices": open_invoices,
            "closed_invoices": closed_invoices,
        },
    )


# --------------------------------------------------------------------------------------
# Workorder + Save/Pay actions
# --------------------------------------------------------------------------------------

@require_POST
@login_required
def sale_save_workorder(request, pk):
    with transaction.atomic():
        """
        Save the POS sale as an Open workorder (for account customers only).
        Walk-in / cash sales never become workorders.

        If a workorder already exists, we allow saving even with 0 POS lines
        so that POS items can be cleared from the workorder.
        """
        sale = get_object_or_404(RetailSale, pk=pk)
        _guard_sale_unlocked(sale)

        # ensure a POS number, but only when actually saving
        _ensure_pos_number(sale)

        if not sale.customer:
            messages.error(request, "Please select a customer before saving as a workorder.")
            return redirect("retail:sale_detail", pk=sale.pk)

        if _is_walkin_customer(sale.customer):
            # Walk-in: no workorder – just stay on POS
            return redirect("retail:sale_detail", pk=sale.pk)

        # 🔹 Only block empty sales when there is NO workorder yet.
        if not sale.lines.exists() and not getattr(sale, "workorder_id", None):
            messages.error(request, "Please add at least one line item before saving.")
            return redirect("retail:sale_detail", pk=sale.pk)

        try:
            wo = _ensure_sale_workorder(sale)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("retail:sale_detail", pk=sale.pk)

        if wo is None:
            # Safety fallback; shouldn't happen with non-walkin customers
            return redirect("retail:sale_detail", pk=sale.pk)

        _sync_sale_lines_to_workorder(sale, wo)

        messages.success(
            request,
            f"Workorder #{wo.workorder} saved as Open "
            f"({RetailWorkorderItem.objects.filter(workorder=wo, sale=sale).count()} POS items)."
        )
        return redirect("workorders:overview", id=wo.workorder)


@require_POST
@login_required
def sale_pay_workorder(request, pk):
    """
    Pay flow:
    - Walk-in / cash: no workorder, record RetailCashSale and mark as paid.
    - Account customer: ensure workorder + sync items, then go into normal workflow.
    """
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    cust = sale.customer

    # Must have at least one line
    if not sale.lines.exists():
        messages.error(request, "Please add at least one line item before taking payment.")
        return redirect("retail:sale_detail", pk=sale.pk)

    # Must have a customer (including Walk-in)
    if not cust:
        messages.error(request, "Please select a customer before taking payment.")
        return redirect("retail:sale_detail", pk=sale.pk)

    # Compute POS totals
    subtotal, tax, total = _compute_sale_totals(sale)

    # CASE 1: Walk-in / cash sale — NO workorder, just a RetailCashSale record
    if _is_walkin_customer(cust):
        cash_record, created = RetailCashSale.objects.get_or_create(
            sale=sale,
            defaults={
                "customer": cust,
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "payment_method": "Cash",
                "created_by": request.user,
            },
        )
        if not created:
            cash_record.subtotal = subtotal
            cash_record.tax = tax
            cash_record.total = total
            cash_record.save(update_fields=["subtotal", "tax", "total"])

        # Optionally mark the sale as paid here
        sale.save()

        messages.success(request, f"Cash sale recorded. Total: {total}")
        return redirect("retail:sale_detail", pk=sale.pk)

    # CASE 2: Account customer — create/ensure Workorder + sync lines
    try:
        wo = _ensure_sale_workorder(sale)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("retail:sale_detail", pk=sale.pk)

    if wo is None:
        messages.error(request, "Unable to create workorder for this sale.")
        return redirect("retail:sale_detail", pk=sale.pk)

    _sync_sale_lines_to_workorder(sale, wo)

    messages.success(request, f"Workorder #{wo.workorder} created for payment.")
    # You can later redirect straight into a receive-payment screen
    return redirect("workorders:overview", id=wo.workorder)


# --------------------------------------------------------------------------------------
# Small POS helpers (notes, customer block, header, footer)
# --------------------------------------------------------------------------------------

@require_POST
@login_required
def update_sale_notes(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)
    notes = (request.POST.get("notes") or "").strip()
    sale.notes = notes
    sale.save(update_fields=["notes"])
    return HttpResponse("", status=204)


@login_required
def sale_customer_block(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    customers = Customer.objects.filter(active=True).order_by("company_name")
    html = render_to_string(
        "retail/partials/customer_block.html",
        {"sale": sale, "customers": customers, "customer": sale.customer},
        request=request,
    )
    return HttpResponse(html)


@login_required
def sale_header_actions(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    return render(request, "retail/partials/sale_header_actions.html", {"sale": sale})


@login_required
def sale_totals_actions(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    return render(request, "retail/partials/totals_actions.html", {"sale": sale})


@login_required
def sale_payment_modal(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)
    subtotal, tax, total = _compute_sale_totals(sale)

    form = PaymentMethodForm()

    return render(
        request,
        "retail/partials/payment_modal.html",
        {
            "sale": sale,
            "form": form,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
        },
    )


@login_required
@require_POST
def sale_payment_submit(request, pk):
    with transaction.atomic():
        sale = get_object_or_404(RetailSale, pk=pk)
        _guard_sale_unlocked(sale)

        # ensure a POS number the first time it’s paid
        _ensure_pos_number(sale)

        # If already locked/paid, just bounce back – no double-pay
        if sale.locked:
            resp = HttpResponse("")
            resp["HX-Redirect"] = reverse("retail:sale_detail", args=[sale.pk])
            return resp

        form = PaymentMethodForm(request.POST)

        if not form.is_valid():
            # Re-render modal with errors
            subtotal, tax, total = _compute_sale_totals(sale)
            return render(
                request,
                "retail/partials/payment_modal.html",
                {
                    "sale": sale,
                    "form": form,
                    "subtotal": subtotal,
                    "tax": tax,
                    "total": total,
                },
            )

        payment_method = form.cleaned_data["payment_method"]
        amount = form.cleaned_data["amount"]          # what the user typed
        notes = form.cleaned_data.get("notes") or ""
        check_number = form.cleaned_data.get("check_number")

        # If a check number was entered, prepend it to notes
        if check_number:
            prefix = f"Check #{check_number}"
            notes = f"{prefix} — {notes}" if notes else prefix

        subtotal, tax, total = _compute_sale_totals(sale)
        cust = sale.customer

        # --- scale factor for partial refunds (used for both AR + ledger) ---
        scale_for_ledger = Decimal("1.0")
        if sale.is_refund:
            max_refund = abs(total)
            if amount is None:
                refund_amount = max_refund
            else:
                refund_amount = abs(Decimal(amount))

            if max_refund > 0 and refund_amount > max_refund:
                refund_amount = max_refund

            if max_refund > 0:
                scale_for_ledger = (refund_amount / max_refund).quantize(Decimal("0.0001"))
            else:
                scale_for_ledger = Decimal("0")

        # 🔹 If no customer is set at all, treat it as Walk-in / Cash
        if cust is None:
            walkin, _ = Customer.objects.get_or_create(
                company_name="Walk-in / Cash Sale",
                defaults={
                    "first_name": "Walk-in",
                    "last_name": "Customer",
                    "address1": "",
                    "address2": "",
                    "city": "",
                    "state": "",
                    "zipcode": "",
                    "phone1": "",
                    "phone2": "",
                    "email": "",
                    "website": "",
                    "po_number": "",
                    "customer_number": "WALKIN",
                    "avg_days_to_pay": "",
                },
            )
            cust = walkin
            sale.customer = walkin
            # default to taxable walk-in if nothing set yet
            if sale.tax_rate is None or sale.tax_rate == 0:
                sale.tax_exempt = False
                sale.tax_rate = Decimal("0.055")
            sale.save(update_fields=["customer", "tax_exempt", "tax_rate"])

        # 🔹 Walk-in / cash path: record RetailCashSale, no workorder
        if _is_walkin_customer(cust):
            if sale.is_refund:
                kind = "Refund"
            else:
                kind = "Sale"

            # For walk-ins, we treat the typed amount as the actual cash movement.
            # Refunds should be negative in reports.
            if amount is None:
                amount = total  # fallback to full total if somehow missing
            signed_total = Decimal(amount)
            if sale.is_refund:
                signed_total = -abs(signed_total)

            cash_record, created = RetailCashSale.objects.get_or_create(
                sale=sale,
                defaults={
                    "customer": cust,
                    "subtotal": subtotal,
                    "tax": tax,
                    "total": signed_total,
                    "payment_method": payment_method,
                    "payment_notes": f"{kind}: {notes}",
                    "created_by": request.user,
                },
            )
            if not created:
                cash_record.subtotal = subtotal
                cash_record.tax = tax
                cash_record.total = signed_total
                cash_record.payment_method = payment_method
                cash_record.payment_notes = f"{kind}: {notes}"
                cash_record.save(
                    update_fields=["subtotal", "tax", "total", "payment_method", "payment_notes"]
                )

            sale.status = "paid"
            sale.locked = True
            if not sale.paid_at:
                sale.paid_at = timezone.now()
            sale.save(update_fields=["status", "locked", "paid_at"])

            # 🔹 Ledger entries for POS sale/refund (respect partial refunds)
            _record_pos_ledger_entries(sale, scale=scale_for_ledger)

            messages.success(request, f"{kind} recorded for {signed_total}.")
            resp = HttpResponse("")
            resp["HX-Redirect"] = reverse("retail:sale_detail", args=[sale.pk])
            return resp

        # 🔹 Account customer path: ensure workorder & hand off to AR flow
        wo = _ensure_sale_workorder(sale)
        if not wo:
            messages.error(request, "Unable to create workorder for this sale.")
            resp = HttpResponse("")
            resp["HX-Redirect"] = reverse("retail:sale_receipt", args=[sale.pk])
            return resp

        # Make sure the sale is linked to this workorder
        if sale.workorder_id is None:
            sale.workorder = wo
            sale.save(update_fields=["workorder"])

        # Mirror POS line items onto the workorder so overview shows each line
        _sync_sale_lines_to_workorder(sale, wo)

        # 🔹 If this is a refund, apply a *partial* POS adjustment based on entered amount
        if sale.is_refund:
            full_subtotal, full_tax, full_total = _compute_sale_totals(sale)

            base_subtotal = abs(full_subtotal)
            base_tax = abs(full_tax)

            refund_subtotal = (base_subtotal * scale_for_ledger).quantize(Decimal("0.01"))
            refund_tax = (base_tax * scale_for_ledger).quantize(Decimal("0.01"))

            apply_pos_adjustment_to_workorder(
                workorder=wo,
                amount=-refund_subtotal,
                tax_amount=-refund_tax,
            )

        # 🔹 Recompute full workorder totals after sync/adjustment
        totals = compute_workorder_totals(wo)
        wo.subtotal = f"{totals.subtotal:.2f}"
        wo.tax = f"{totals.tax:.2f}"
        wo.workorder_total = f"{totals.total:.2f}"
        wo.total_balance = totals.total
        wo.open_balance = totals.total
        wo.save(
            update_fields=[
                "subtotal",
                "tax",
                "workorder_total",
                "total_balance",
                "open_balance",
            ]
        )

        sale.status = "paid"
        if not sale.paid_at:
            sale.paid_at = timezone.now()
        sale.locked = True
        sale.save(update_fields=["status", "locked", "paid_at"])

        # 🔹 Ledger entries for POS sale/refund (account customers, partial-aware)
        _record_pos_ledger_entries(sale, scale=scale_for_ledger)

        completed_status = JobStatus.objects.filter(name__iexact="Completed").first()
        if completed_status:
            wo.workorder_status = completed_status
            wo.save(update_fields=["workorder_status"])

        resp = HttpResponse("")
        resp["HX-Redirect"] = reverse("retail:sale_receipt", args=[sale.pk])
        return resp

@login_required
def sale_refund_start(request, pk):
    original = get_object_or_404(RetailSale, pk=pk)

    if not original.locked or original.status != "paid":
        return HttpResponse(
            "Only paid/locked POS sales can be refunded.",
            status=400,
        )

    with transaction.atomic():
        refund = _create_refund_sale_from(original, request.user)

    # Just redirect to the refund POS screen; no modal needed after this
    return redirect("retail:sale_detail", pk=refund.pk)

def _create_refund_sale_from(original: RetailSale, user) -> RetailSale:
    """
    Create a new RetailSale that represents a refund of `original`.

    - Same customer / internal_company / workorder link.
    - Lines copied with NEGATIVE qty so totals are negative.
    """
    refund = RetailSale.objects.create(
        customer=original.customer,
        internal_company=original.internal_company,
        workorder=original.workorder,
        is_refund=True,
        original_sale=original,
        status="open",
        locked=False,
        notes=f"Refund for POS sale #{original.id}",
    )

    for line in original.lines.all():
        RetailSaleLine.objects.create(
            sale=refund,
            inventory=line.inventory,
            description=line.description,
            qty=-line.qty,               # 👈 negative
            unit_price=line.unit_price,
            # copy any other fields you need (tax flags, etc.)
        )

    return refund

@login_required
def refund_lookup(request):
    if request.method == "POST":
        form = RefundLookupForm(request.POST)
        if not form.is_valid():
            return render(request, "retail/refund_lookup.html", {"form": form})

        number = form.cleaned_data["invoice_number"].strip()

        # If you're using a dedicated pos_number: sale = get_object_or_404(RetailSale, pos_number=number)
        try:
            sale = RetailSale.objects.get(id=number)
        except RetailSale.DoesNotExist:
            messages.error(request, f"POS sale {number} not found.")
            return render(request, "retail/refund_lookup.html", {"form": form})

        if not sale.locked or sale.status != "paid":
            messages.error(request, "Only paid POS sales can be refunded.")
            return render(request, "retail/refund_lookup.html", {"form": form})

        return redirect("retail:sale_refund_start", pk=sale.pk)
    else:
        form = RefundLookupForm()

    return render(request, "retail/refund_lookup.html", {"form": form})

@login_required
def pos_sale_list(request):
    """
    Simple POS sales list:
    - one row per RetailSale
    - also shows negative + low stock warnings
    """
    sales = (
        RetailSale.objects
        .select_related("customer", "cashier")
        .order_by("-created_at", "-id")
    )

    # You can tweak this low_stock_threshold number as needed
    low_stock_threshold = Decimal("5")

    negative_items, low_items = get_stock_alerts(
        negative_threshold=Decimal("0"),
        low_threshold=low_stock_threshold,
    )

    context = {
        "sales": sales,
        "negative_items": negative_items,
        "low_items": low_items,
        "low_stock_threshold": low_stock_threshold,
    }
    return render(request, "retail/pos_sale_list.html", context)

@login_required
@require_POST
def sale_toggle_tax(request, pk):
    """
    Toggle tax just for this sale:
    - Does NOT change the customer's tax_exempt setting.
    - When tax is off, tax_exempt=True and tax_rate=0.
    - When tax is on, tax_exempt=False and tax_rate defaults to 5.5% if empty.
    """
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    if sale.tax_exempt:
        # Turn tax back ON for this sale
        sale.tax_exempt = False
        if not sale.tax_rate or sale.tax_rate == 0:
            sale.tax_rate = Decimal("0.055")  # WI 5.5% default
    else:
        # Turn tax OFF just for this sale
        sale.tax_exempt = True
        sale.tax_rate = Decimal("0.000")

    sale.save(update_fields=["tax_exempt", "tax_rate"])

    return redirect("retail:sale_detail", sale.pk)

@login_required
@require_POST
def sale_send_as_quote(request, pk):
    """
    Create a quote-style workorder from this POS sale and sync lines.
    Does NOT mark the sale as paid; just mirrors POS into a quote.
    """
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    wo = _ensure_sale_workorder(sale, as_quote=True)
    if not wo:
        messages.error(request, "Unable to create quote for this sale.")
        return redirect("retail:sale_detail", sale.pk)

    _sync_sale_lines_to_workorder(sale, wo)

    messages.success(request, f"Quote {wo.workorder} created from POS sale.")
    return redirect("workorders:overview", id=wo.workorder)

@require_POST
@login_required
def sale_add_custom_line(request, pk):
    """
    Add a one-off custom line to a POS sale
    (no InventoryMaster link, just description + price).
    """
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    desc = (request.POST.get("description") or "").strip()
    qty_raw = request.POST.get("qty") or "1"
    price_raw = request.POST.get("unit_price") or "0"

    if not desc:
        messages.error(request, "Please enter a description for the custom item.")
        return redirect("retail:sale_detail", pk=sale.pk)

    try:
        qty = Decimal(qty_raw)
        unit_price = Decimal(price_raw)
    except Exception:
        messages.error(request, "Invalid quantity or price.")
        return redirect("retail:sale_detail", pk=sale.pk)

    RetailSaleLine.objects.create(
        sale=sale,
        inventory=None,
        description=desc,
        qty=qty,
        unit_price=unit_price,
        # line_total will be calculated in your totals logic or via model save
    )

    messages.success(request, f"Custom item '{desc}' added.")
    return redirect("retail:sale_detail", pk=sale.pk)

@login_required
def sale_receipt(request, pk):
    """
    Printable receipt for a POS sale (works for both walk-in and account).

    - If there's a RetailCashSale → show payment details (cash/check/card).
    - If it's an account sale → show that it was charged to account / workorder.
    """
    sale = get_object_or_404(RetailSale, pk=pk)

    # sale.lines related_name, or fallback to default
    lines_qs = getattr(sale, "lines", None) or sale.retailsaleline_set
    lines = list(lines_qs.all())

    subtotal, tax, total = _compute_sale_totals(sale)
    cash = getattr(sale, "cash_record", None)  # RetailCashSale or None

    context = {
            "sale": sale,
            "lines": lines,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "cash": cash,  # None for account sales
        }

        # If called via HTMX (for the modal), render modal partial instead of full page
    if getattr(request, "htmx", False):
        return render(request, "retail/modals/receipt_modal.html", context)

    # Normal full-page printable receipt
    return render(request, "retail/receipt.html", context)

@login_required
def retail_pricing_admin(request):
    items = (
        InventoryMaster.objects
        .filter(retail=True, active=True)
        .select_related("retail_category")
        .order_by("name")
    )

    # Optional editing logic can go here (POST to update one row)
    paginator = Paginator(items, 50)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    context = {
        "page_obj": page_obj,
        "compute_retail_price": compute_retail_price,
    }
    return render(request, "inventory/retail_pricing_admin.html", context)

@require_POST
@login_required
def sale_update_line_price(request, sale_pk, line_pk):
    sale = get_object_or_404(RetailSale, pk=sale_pk)
    _guard_sale_unlocked(sale)

    line = get_object_or_404(RetailSaleLine, pk=line_pk, sale=sale)

    qty_str = request.POST.get("qty")
    raw_price = request.POST.get("unit_price")
    update_default = bool(request.POST.get("update_default_price"))

    # --- qty (optional, fall back to existing) ---
    if qty_str is not None:
        try:
            line.qty = Decimal(qty_str)
        except (InvalidOperation, TypeError):
            # bad input – keep existing qty
            pass

    # --- price (optional, fall back to existing) ---
    new_price = None
    if raw_price is not None:
        try:
            new_price = Decimal(raw_price)
        except (InvalidOperation, TypeError, ValueError):
            new_price = None

    if new_price is not None:
        line.unit_price = new_price

    # keep any existing line_total field in sync if you have it
    if hasattr(line, "line_total"):
        qty = line.qty or Decimal("0")
        price = line.unit_price or Decimal("0")
        line.line_total = qty * price

    line.save()

    # --- optionally update default retail pricing override for this item ---
    if update_default and line.inventory_id:
        inv = line.inventory

        # get or create the pricing row without nuking existing override unless we set it
        rp = ensure_retail_pricing(inv, reset_override=False)

        # store the POS override as the new "override price"
        rp.override_price = line.unit_price

        # keep purchase / calculated in sync (optional but nice)
        rp.purchase_price = inv.unit_cost or Decimal("0.00")
        rp.calculated_price = compute_retail_price(inv)
        rp.save()

    # figure out row number for "#" column
    line_ids = list(
        sale.lines.order_by("id").values_list("id", flat=True)
    )
    try:
        rownum = line_ids.index(line.id) + 1
    except ValueError:
        rownum = 1

    # HTMX request => return updated row partial
    if request.headers.get("HX-Request") == "true":
        resp = render(
            request,
            "retail/partials/line_row.html",
            {"sale": sale, "line": line, "rownum": rownum},
        )
        # tell totals panel to refresh itself
        resp["HX-Trigger"] = "retail-totals-changed"
        return resp

    # non-HTMX fallback
    messages.success(request, "Line updated.")
    return redirect("retail:sale_detail", pk=sale.pk)

@require_POST
@login_required
def sale_update_line_variation(request, sale_pk, line_pk):
    sale = get_object_or_404(RetailSale, pk=sale_pk)
    _guard_sale_unlocked(sale)

    line = get_object_or_404(RetailSaleLine, pk=line_pk, sale=sale)

    variation_id = request.POST.get("variation_id") or ""
    rownum = request.POST.get("rownum") or "0"

    if variation_id:
        try:
            v = InventoryQtyVariations.objects.get(pk=variation_id, inventory=line.inventory)
            line.sold_variation = v
        except InventoryQtyVariations.DoesNotExist:
            line.sold_variation = None
    else:
        line.sold_variation = None

    line.save()

    html = render_to_string(
        "retail/partials/line_row.html",
        {
            "sale": sale,
            "line": line,
            "rownum": rownum,
        },
        request=request,
    )
    return HttpResponse(html)

@login_required
def pos_qty_sold_report(request):
    """
    POS Qty Sold report, driven by InventoryLedger + helper.

    - Filters by date range (ledger.when)
    - Uses source_type POS_SALE / POS_REFUND
    - Net sold = -SUM(qty_delta)
    """
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    default_end = today

    start_str = request.GET.get("start") or ""
    end_str = request.GET.get("end") or ""

    def _parse_date(val, default):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except Exception:
            return default

    start_date = _parse_date(start_str, default_start)
    end_date = _parse_date(end_str, default_end)

    rows = get_qty_sold_summary(start_date=start_date, end_date=end_date)

    context = {
        "rows": rows,
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
    }
    return render(request, "retail/reports/pos_qty_sold_report.html", context)

@login_required
def pos_qty_sold_item_detail(request, item_id):
    """
    Drill-down for a single item:

    - Shows ledger rows for POS_SALE / POS_REFUND
    - Same date range pattern as the main POS Qty Sold report
    """
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    default_end = today

    start_str = request.GET.get("start") or ""
    end_str = request.GET.get("end") or ""

    def _parse_date(val, default):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except Exception:
            return default

    start_date = _parse_date(start_str, default_start)
    end_date = _parse_date(end_str, default_end)

    start_dt = datetime.combine(start_date, datetime.min.time()).replace(microsecond=0)
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0)

    item = get_object_or_404(InventoryMaster, pk=item_id)

    entries = (
        InventoryLedger.objects
        .filter(
            inventory_item=item,
            source_type__in=["POS_SALE", "POS_REFUND"],
            when__gte=start_dt,
            when__lte=end_dt,
        )
        .order_by("-when")
    )

    # net sold in this period = -sum(qty_delta)
    agg = entries.aggregate(qty_delta_sum=Sum("qty_delta"))
    qty_delta_sum = agg["qty_delta_sum"] or 0
    net_sold = -qty_delta_sum

    context = {
        "item": item,
        "entries": entries,
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
        "net_sold": net_sold,
        "on_hand": get_on_hand(item),
    }
    return render(request, "retail/reports/pos_qty_sold_item_detail.html", context)

@login_required
def inventory_variation_modal(request, sale_pk, inventory_pk):
    """
    Show a modal that lets the cashier pick a variation + quantity
    before adding a line to a POS sale.
    """
    sale = get_object_or_404(RetailSale, pk=sale_pk)
    _guard_sale_unlocked(sale)

    item = get_object_or_404(InventoryMaster, pk=inventory_pk)
    variations = InventoryQtyVariations.objects.filter(inventory=item).order_by("id")

    # If no variations, we still let them enter qty as base units.
    context = {
        "sale": sale,
        "item": item,
        "variations": variations,
    }
    return render(request, "retail/modals/inventory_variation_modal.html", context)

@login_required
def sale_receipt_modal(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)

    lines_qs = getattr(sale, "lines", None) or sale.retailsaleline_set
    lines = list(lines_qs.all())

    subtotal, tax, total = _compute_sale_totals(sale)
    cash = getattr(sale, "cash_record", None)  # RetailCashSale or None

    context = {
        "sale": sale,
        "lines": lines,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "cash": cash,
    }

    return render(request, "retail/modals/receipt_modal.html", context)

@require_POST
@login_required
def sale_toggle_delivery(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    # Turn OFF
    if sale.requires_delivery:
        sale.requires_delivery = False
        sale.save()

        Delivery.objects.filter(
            sale=sale,
            status=STATUS_PENDING,
        ).update(status=STATUS_CANCELLED)

        sync_workorder_delivery_from_sale(sale)  # will clear requires_delivery/delivery_date
        delivery_date = None

    # Turn ON
    else:
        sale.requires_delivery = True
        sale.save()

        scheduled_date = get_sticky_delivery_date(request)

        delivery = ensure_sale_delivery(sale, scheduled_date)
        ensure_route_entry_for_customer(delivery)  # your existing helper

        set_sticky_delivery_date(request, scheduled_date)
        sync_workorder_delivery_from_sale(sale, scheduled_date)

        delivery_date = scheduled_date

    html = render_to_string(
        "retail/partials/sale_delivery_block.html",
        {"sale": sale, "delivery_date": delivery_date},
        request=request,
    )
    return HttpResponse(html)

@login_required
def delivery_report(request):
    date_str = request.GET.get("date") or ""
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    deliveries_sorted = _get_sorted_deliveries_for_date(selected_date)

    context = {
        "selected_date": selected_date,
        "deliveries": deliveries_sorted,
    }
    return render(request, "retail/delivery_report.html", context)


def _adjust_delivery_order(move: str, delivery_id: str) -> None:
    try:
        delivery = Delivery.objects.select_related("customer").get(pk=delivery_id)
    except Delivery.DoesNotExist:
        return

    customer = delivery.customer
    if not customer:
        return

    entry = ensure_route_entry_for_customer(customer)

    # Load all entries in current order
    entries = list(
        DeliveryRouteEntry.objects
        .select_related("customer")
        .order_by("sort_order", "customer__company_name")
    )

    if not entries:
        return

    # 🔧 Normalize sort_order to 10, 20, 30, ... based on current order
    changed_any = False
    for idx, e in enumerate(entries):
        desired = (idx + 1) * 10
        if e.sort_order != desired:
            e.sort_order = desired
            changed_any = True

    if changed_any:
        DeliveryRouteEntry.objects.bulk_update(entries, ["sort_order"])

    # Rebuild the list sorted by the normalized values
    entries.sort(key=lambda e: e.sort_order)

    # Find current index of this customer's entry
    index = None
    for i, e in enumerate(entries):
        if e.pk == entry.pk:
            index = i
            break

    if index is None:
        return

    # Decide which neighbor to swap with
    if move == "up" and index > 0:
        other = entries[index - 1]
    elif move == "down" and index < len(entries) - 1:
        other = entries[index + 1]
    else:
        return

    # Swap the two sort_order values
    entry.sort_order, other.sort_order = other.sort_order, entry.sort_order
    entry.save(update_fields=["sort_order"])
    other.save(update_fields=["sort_order"])

@require_POST
@login_required
def delivery_reorder(request):
    move = request.POST.get("move") or ""
    delivery_id = request.POST.get("delivery_id") or ""
    date_str = request.POST.get("date") or ""
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = timezone.localdate()

    if move and delivery_id:
        _adjust_delivery_order(move, delivery_id)

    deliveries_sorted = _get_sorted_deliveries_for_date(selected_date)

    html = render_to_string(
        "retail/partials/delivery_report_table.html",
        {"selected_date": selected_date, "deliveries": deliveries_sorted},
        request=request,
    )
    return HttpResponse(html)

@require_POST
@login_required
def delivery_update_date(request):
    delivery_id = request.POST.get("delivery_id") or ""
    date_str = request.POST.get("date") or ""
    current_date_str = request.POST.get("current_date") or ""

    # Parse the "report date" – what the page is currently on
    try:
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    except ValueError:
        current_date = timezone.localdate()

    # Parse the *new* scheduled date for this delivery
    new_date = None
    if date_str:
        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            new_date = None

    try:
        delivery = Delivery.objects.select_related("customer").get(pk=delivery_id)
    except Delivery.DoesNotExist:
        # If somehow missing, just rebuild table for current_date
        deliveries_sorted = _get_sorted_deliveries_for_date(current_date)
    else:
        if new_date:
            delivery.scheduled_date = new_date
            delivery.save()
        # After updating a single row, always show the table
        # for the current report date, not the new date
        deliveries_sorted = _get_sorted_deliveries_for_date(current_date)

    html = render_to_string(
        "retail/partials/delivery_report_table.html",
        {"selected_date": current_date, "deliveries": deliveries_sorted},
        request=request,
    )
    return HttpResponse(html)

@require_POST
@login_required
def sale_update_delivery_date(request, pk):
    sale = get_object_or_404(RetailSale, pk=pk)
    _guard_sale_unlocked(sale)

    date_str = request.POST.get("delivery_date") or ""
    try:
        new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        new_date = timezone.localdate()

    # make sure the sale itself is flagged for delivery
    if not sale.requires_delivery:
        sale.requires_delivery = True
        sale.save()

    delivery = ensure_sale_delivery(sale, new_date)

    # sticky default for future sales / workorders
    set_sticky_delivery_date(request, new_date)

    # keep linked workorder in sync, if any
    sync_workorder_delivery_from_sale(sale, new_date)

    html = render_to_string(
        "retail/partials/sale_delivery_block.html",
        {"sale": sale, "delivery_date": new_date},
        request=request,
    )
    return HttpResponse(html)