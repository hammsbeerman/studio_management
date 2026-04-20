import os
import csv
import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, FileResponse, Http404
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Avg, Max, Count, Sum, Subquery, Value, DecimalField, OuterRef, Q, Prefetch
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta, datetime, date
from datetime import date as date_cls
from decimal import Decimal, InvalidOperation
from typing import Tuple
import logging
from .models import AccountsPayable, DailySales, Payments, WorkorderPayment, CreditMemo, WorkorderCreditMemo, GiftCertificate, GiftCertificateRedemption, CreditAdjustment, StatementRun
from .forms import DailySalesForm, AppliedElsewhereForm, PaymentForm, DateRangeForm
from finance.forms import AddInvoiceForm, AddInvoiceItemForm, EditInvoiceForm, BulkEditInvoiceForm, SalesComparisonForm
from finance.models import InvoiceItem
from inventory.services.ledger import record_inventory_movement
from customers.models import Customer
from workorders.models import Workorder
from controls.models import PaymentType, Measurement
from inventory.models import Vendor, InventoryMaster, VendorItemDetail, InventoryQtyVariations, InventoryPricingGroup, Inventory
from inventory.forms import InventoryMasterForm, VendorItemDetailForm
from onlinestore.models import StoreItemDetails
from retail.models import RetailCashSale
from .tasks import build_krueger_bulk_statements
from finance.services.ap_invoice_items import save_ap_invoice_item_from_post
from finance.helpers_ar import (
    q_non_quote as _q_non_quote,
    live_applied_totals as _live_applied_totals,
    live_total_due as _live_total_due,
    live_open_balance as _live_open_balance,
    workorders_base_ar_qs as _workorders_base_ar_qs,
    workorder_billed_date as _workorder_billed_date,
    workorder_aging_days as _workorder_aging_days,
    build_live_ar_rows as _build_live_ar_rows,
    build_live_aging_rows as _build_live_aging_rows,
    ar_open_workorders_qs,
    recompute_customer_open_balance,
    recompute_customer_credit,
    hx_ar_changed_204,
)
from workorders.services.totals import (
    compute_workorder_totals,
    recalc_workorder_balances,
)

logger = logging.getLogger(__file__)




def _money(val) -> Decimal:
    """
    Safe money parsing:
      - Decimal -> Decimal
      - "1,234.56" -> Decimal("1234.56")
      - "" / None -> Decimal("0.00")
    """
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val
    s = str(val).strip().replace(",", "")
    if not s:
        return Decimal("0.00")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def _invoice_total(wo) -> Decimal:
    """
    Invoice total cap for open_balance.
    Prefers parsed workorder_total (CharField), falls back to total_balance (DecimalField).
    """
    wt = _money(getattr(wo, "workorder_total", None))  # CharField
    if wt > 0:
        return wt
    return _money(getattr(wo, "total_balance", None))


def _clamp_balances(wo, proposed_open: Decimal) -> Tuple[Decimal, Decimal, bool]:
    """
    Returns (open_balance, amount_paid, paid_in_full) with invariant:
      0 <= open_balance <= invoice_total
      amount_paid = max(0, invoice_total - open_balance)
    """
    inv = _invoice_total(wo)
    new_open = max(Decimal("0.00"), min(_money(proposed_open), inv))
    new_paid = max(Decimal("0.00"), inv - new_open)
    paid = (new_open == Decimal("0.00") and inv > Decimal("0.00"))
    return new_open, new_paid, paid

def _recalc_avg_days_to_pay(customer_id):
    return (
        Workorder.objects
        .filter(customer_id=customer_id, paid_in_full=1)
        .aggregate(avg=Avg("days_to_pay"))
    )["avg"] or 0

def _days_to_pay(workorder, paid_dt):
    if not workorder.date_billed:
        return 0
    billed_date = workorder.date_billed.date() if hasattr(workorder.date_billed, "date") else workorder.date_billed
    paid_date = paid_dt.date() if hasattr(paid_dt, "date") else paid_dt
    return max((paid_date - billed_date).days, 0)

def _date_range_to_datetimes(start_date, end_date):
    """
    Given two date objects, return (start_dt, end_dt_exclusive)
    as timezone-aware datetimes in the current timezone.

    We then filter with:
        date_billed__gte=start_dt,
        date_billed__lt=end_dt_exclusive
    """
    tz = timezone.get_current_timezone()

    start_dt = timezone.make_aware(
        datetime.combine(start_date, datetime.min.time()),
        tz
    )

    end_next = end_date + timedelta(days=1)
    end_dt_exclusive = timezone.make_aware(
        datetime.combine(end_next, datetime.min.time()),
        tz
    )

    return start_dt, end_dt_exclusive

def _ap_posted_block(request, invoice_obj, *, htmx=False, target_template=None):
    """
    Returns an HttpResponse/redirect if invoice is posted, otherwise None.
    - htmx=True: return an inline alert HTML (or render a template if provided)
    - htmx=False: messages.error + redirect back to invoice detail
    """
    if not getattr(invoice_obj, "posted", False):
        return None

    msg = "This AP invoice is POSTED and cannot be modified. Unpost it first."

    if htmx:
        # If you want to render a partial, pass target_template
        if target_template:
            return render(request, target_template, {"error": msg, "invoice": invoice_obj})
        return HttpResponse(f"""
            <div class="alert alert-danger" role="alert" style="margin-top:10px;">
              {msg}
            </div>
        """)

    messages.error(request, msg)
    return redirect("finance:ap_invoice_detail_id", id=invoice_obj.id)

@login_required
def finance_main(request):
    return render(request, 'finance/main.html')

@login_required
def bill_list(request):
    bills = (
        AccountsPayable.objects
        .filter(void=False)
        .order_by("-invoice_date", "-id")
    )
    return render(request, "finance/AP/view_bills.html", {"bill_list": bills})

@login_required
def ar_dashboard(request):
    customers = Customer.objects.all().order_by("company_name")

    customer_id = (request.GET.get("customer") or "").strip()
    selected_customer = None
    if customer_id.isdigit():
        selected_customer = customers.filter(pk=int(customer_id)).first()

    context = {
        "customers": customers,
        "selected_customer": selected_customer,
        "selected_customer_id": int(customer_id) if customer_id.isdigit() else None,
    }
    return render(request, "finance/AR/ar_dashboard.html", context)


def _base_unit_name_for_item(item: "InventoryMaster") -> str:
    """
    Base unit label for previews / UI.
    InventoryMaster.primary_base_unit is Measurement.
    """
    try:
        if item and item.primary_base_unit and getattr(item.primary_base_unit, "name", None):
            return str(item.primary_base_unit.name)
    except Exception:
        pass
    return "Base unit"

def _to_decimal_or_none(v):
    """
    Workorder.subtotal and workorder_total are CharFields in this project.
    Convert safely for comparisons/formatting; return None if not parseable.
    """
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    s = s.replace(",", "").replace("$", "")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


@login_required
def open_workorders(request):
    customer_id = request.GET.get("customer") or request.GET.get("customers")
    aging_filter = (request.GET.get("aging") or "").strip()

    customers = Customer.objects.all().order_by("company_name")

    if not customer_id:
        return render(
            request,
            "finance/AR/partials/open_workorder_list.html",
            {
                "workorders": [],
                "customer": None,
                "customers": customers,
                "aging_filter": aging_filter,
                "summary": {
                    "total_open": Decimal("0.00"),
                    "current": Decimal("0.00"),
                    "thirty": Decimal("0.00"),
                    "sixty": Decimal("0.00"),
                    "ninety": Decimal("0.00"),
                    "onetwenty": Decimal("0.00"),
                },
            },
        )

    selected_customer = get_object_or_404(Customer, id=customer_id)

    base_qs = (
        Workorder.objects
        .filter(customer_id=customer_id)
        .filter(billed=True)
        .exclude(void=True)
        .filter(_q_non_quote())
        .order_by("-workorder")
    )

    workorders = []
    today_date = timezone.localdate()

    summary = {
        "total_open": Decimal("0.00"),
        "current": Decimal("0.00"),
        "thirty": Decimal("0.00"),
        "sixty": Decimal("0.00"),
        "ninety": Decimal("0.00"),
        "onetwenty": Decimal("0.00"),
    }

    def bucket_for_days(days):
        if days < 30:
            return "current"
        elif days < 60:
            return "30"
        elif days < 90:
            return "60"
        elif days < 120:
            return "90"
        return "120+"

    for wo in base_qs:
        live = _live_open_balance(wo)

        if live["open_bal"] <= Decimal("0.00"):
            continue

        billed_date = _workorder_billed_date(wo)
        aging_days = _workorder_aging_days(wo, today_date=today_date)
        aging_bucket = bucket_for_days(aging_days)

        # summary totals always reflect all open items for customer
        summary["total_open"] += live["open_bal"]
        if aging_bucket == "current":
            summary["current"] += live["open_bal"]
        elif aging_bucket == "30":
            summary["thirty"] += live["open_bal"]
        elif aging_bucket == "60":
            summary["sixty"] += live["open_bal"]
        elif aging_bucket == "90":
            summary["ninety"] += live["open_bal"]
        else:
            summary["onetwenty"] += live["open_bal"]

        # apply requested filter to table rows
        if aging_filter and aging_filter != aging_bucket:
            continue

        wo.total_due_calc = live["total_due"]
        wo.amount_paid_calc = live["total_applied"]
        wo.open_balance_calc = live["open_bal"]
        wo.date_billed_calc = billed_date
        wo.date_paid_calc = getattr(wo, "date_paid", None)
        wo.aging_days_calc = aging_days
        wo.aging_bucket_calc = aging_bucket

        workorders.append(wo)

    context = {
        "customer": selected_customer,
        "customers": customers,
        "workorders": workorders,
        "aging_filter": aging_filter,
        "summary": summary,
    }
    return render(request, "finance/AR/partials/open_workorder_list.html", context)

@login_required
def closed_workorders(request, cust):
    selected_customer = get_object_or_404(Customer, id=cust)

    base_qs = (
        Workorder.objects
        .filter(customer_id=cust)
        .filter(billed=True)
        .exclude(void=True)
        .filter(_q_non_quote())
        .order_by("-workorder")
    )

    workorders = []
    total_days_to_pay = 0
    days_to_pay_count = 0

    for wo in base_qs:
        live = _live_open_balance(wo)

        if live["open_bal"] == Decimal("0.00") and live["total_due"] > Decimal("0.00"):
            billed_date = _workorder_billed_date(wo)
            paid_date = getattr(wo, "date_paid", None)

            if billed_date and paid_date:
                if hasattr(paid_date, "date"):
                    paid_date = paid_date.date()
                days_to_pay = max((paid_date - billed_date).days, 0)
                total_days_to_pay += days_to_pay
                days_to_pay_count += 1
            else:
                days_to_pay = None

            wo.total_due_calc = live["total_due"]
            wo.amount_paid_calc = live["total_applied"]
            wo.open_balance_calc = live["open_bal"]
            wo.date_billed_calc = billed_date
            wo.date_paid_calc = paid_date
            wo.days_to_pay_calc = days_to_pay

            workorders.append(wo)

    avg_days_to_pay = None
    if days_to_pay_count:
        avg_days_to_pay = round(total_days_to_pay / days_to_pay_count, 1)

    context = {
        "customer": selected_customer,
        "workorders": workorders,
        "avg_days_to_pay": avg_days_to_pay,
        "days_to_pay_count": days_to_pay_count,
    }
    return render(request, "finance/AR/partials/closed_workorder_list.html", context)

# @login_required
# def recieve_payment(request):
#     paymenttype = PaymentType.objects.all()
#     customers = Customer.objects.all().order_by('company_name')
#     if request.method == "POST":
#             modal = request.POST.get('modal')
#             id_list = request.POST.getlist('payment')
#             payment_total = 0
#             for x in id_list:
#                 print('payment total')
#                 print(payment_total)
#                 t = Workorder.objects.get(pk=int(x))
#                 balance = t.open_balance
#                 payment_total = payment_total + balance
#             amount = request.POST.get('amount')
#             amount = Decimal(amount)
#             if payment_total > amount:
#                 form = PaymentForm
#                 customer = request.POST.get('customer')
#                 # context = {
#                 #     'paymenttype':paymenttype,
#                 #     'customers':customers,
#                 #     'form': form,
#                 # }
#                 return redirect('finance:open_invoices_recieve_payment', pk=customer, msg=1)
#             # for x in id_list:
#             #     Workorder.objects.filter(pk=int(x)).update(paid_in_full=True)
#             print('testing123')
#             customer = request.POST.get('customer')
#             print(customer)
#             check = request.POST.get('check_number')
#             giftcard = request.POST.get('giftcard_number')
#             refund = request.POST.get('refunded_invoice_number')
#             date = request.POST.get('date')
#             #date = date.datetime('%Y-%m-%d')
#             #date = datetime.strptime(date, '%Y/%m/%d').date()
#             date = datetime.strptime(date, '%m/%d/%Y')
#             print(date)
#             form = PaymentForm(request.POST)
#             if form.is_valid():
#                 obj = form.save(commit=False)
#                 obj.check_number = check
#                 print(obj.check_number)
#                 obj.giftcard_number = giftcard
#                 obj.refunded_invoice_number = refund
#                 obj.save()
#                 print('Payment ID')
#                 payment_id = obj.pk
#                 remainder = amount
#                 payment_date = date.date()
#                 print(date)
#                 print(amount)
#                 for x in id_list:
#                     #Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, paid_in_full = full_payment, date_paid = date)
#                     amount = Workorder.objects.get(pk=int(x))
#                     #Most of this fiddlefuckery is to convert datetimes to date
#                     date_billed = amount.date_billed
#                     date_billed = date_billed.replace(tzinfo=None)
#                     date_billed = date_billed.date()
#                     days_to_pay = payment_date - date_billed
#                     print(payment_date)
#                     days_to_pay = abs((days_to_pay).days)
#                     Workorder.objects.filter(pk=int(x)).update(paid_in_full=1, date_paid=date, open_balance=0, amount_paid = amount.total_balance, days_to_pay = days_to_pay, payment_id = payment_id)
#                     remainder = remainder - amount.open_balance
#                     print('Remainder')
#                     print(remainder)
#                     #Save Payment History
#                     p = WorkorderPayment(workorder_id=int(x), payment_id=payment_id, payment_amount=amount.total_balance, date=payment_date)
#                     print()
#                     print(payment_date)
#                     p.save()
#                 print(remainder)
#                 Payments.objects.filter(pk=payment_id).update(available=remainder)
#                 # if remainder > 0:
#                 #     Payments.objects.filter(pk=payment_id).update(available=remainder)
#                 # else:
#                 #     Payments.objects.filter(pk=payment_id).update(available=remainder)
#                 print(customer)
#                 cust = Customer.objects.get(id=customer)
#                 try:
#                     credit = cust.credit + obj.amount
#                 except: 
#                     credit = obj.amount
#                 credit = credit - payment_total
#                 open_balance = Workorder.objects.filter(customer_id=customer).exclude(completed=0).exclude(paid_in_full=1).aggregate(sum=Sum('open_balance'))
#                 open_balance = list(open_balance.values())[0]
#                 print(open_balance)
#                 balance = open_balance
#                 if not balance:
#                     balance = 0
#                 high_balance = cust.high_balance
#                 if not high_balance:
#                     high_balance = 0
#                  #   high_balance = open_balance - credit             
#                 print(high_balance)
#                 if high_balance > balance:
#                     high_balance = high_balance
#                 else:
#                     high_balance = balance
#                 print(high_balance)
#                 Customer.objects.filter(pk=customer).update(credit=credit, open_balance=open_balance, high_balance=high_balance)
#                 if modal == '1':
#                     workorders = Workorder.objects.filter(customer=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
#                     total_balance = workorders.filter().aggregate(Sum('open_balance'))
#                     credits = Customer.objects.get(pk=customer)
#                     credits = credits.credit
#                     print(credits)
#                     #customer = customer
#                     print(customer)
#                     # context = {
#                     #     'pk': customer,
#                     #     'customer':customer,
#                     #     'total_balance':total_balance,
#                     #     'credit':credits,
#                     #     'workorders':workorders,
#                     # }
#                     credits = Customer.objects.get(pk=customer)
#                     credits = credits.credit
#                     if credits:
#                         return redirect('finance:open_invoices', pk=customer)
#                     else:
#                         workorders = Workorder.objects.filter(customer=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).order_by('workorder')
#                         if workorders:
#                             return redirect('finance:open_invoices', pk=customer)
#                         #Update paid status
#                         return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderVoid'})
#                 else:
#                     return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
#     form = PaymentForm
#     context = {
#         'paymenttype':paymenttype,
#         'customers':customers,
#         'form': form,
#     }
#     return render(request, 'finance/AR/modals/recieve_payment.html', context)

@login_required
@transaction.atomic
def recieve_payment(request):
    paymenttype = PaymentType.objects.all()
    customers = Customer.objects.all().order_by("company_name")

    selected_customer_id = request.GET.get("customer") or request.GET.get("customers")
    selected_customer_id = int(selected_customer_id) if str(selected_customer_id).isdigit() else None

    if request.method != "POST":
        return render(
            request,
            "finance/AR/modals/recieve_payment.html",
            {
                "paymenttype": paymenttype,
                "customers": customers,
                "form": PaymentForm,
                "selected_customer_id": selected_customer_id,
            },
        )

    customer_id = request.POST.get("customer")
    id_list = request.POST.getlist("payment")

    if not (customer_id and str(customer_id).isdigit()):
        return HttpResponseBadRequest("Invalid customer")

    customer = get_object_or_404(Customer, pk=int(customer_id))

    def _modal_error(msg):
        return HttpResponse(msg, status=400)

    # --- amount ---
    try:
        pay_amount = Decimal(request.POST.get("amount", "0")).quantize(Decimal("0.01"))
    except:
        return _modal_error("Invalid amount")

    if pay_amount <= 0:
        return _modal_error("Amount must be > 0")

    # --- date ---
    raw_date = request.POST.get("date")
    try:
        payment_date = datetime.strptime(raw_date, "%m/%d/%Y").date()
    except:
        try:
            payment_date = date_cls.fromisoformat(raw_date)
        except:
            payment_date = timezone.localdate()

    # --- selected workorders ---
    wo_ids = [int(x) for x in id_list if str(x).isdigit()]

    workorders = list(
        Workorder.objects.select_for_update()
        .filter(pk__in=wo_ids, customer=customer)
        .exclude(billed=0)
        .filter(_q_non_quote())
        .exclude(void=1)
    ) if wo_ids else []

    # --- compute live balances ---
    live_open = {}
    selected_total = Decimal("0.00")

    for wo in workorders:
        live = _live_open_balance(wo)
        live_open[wo.pk] = live["open_bal"]
        selected_total += live["open_bal"]

    # must cover selected invoices
    if workorders and selected_total > pay_amount:
        return _modal_error("Payment less than selected invoices")

    # --- create payment ---
    form = PaymentForm(request.POST)
    if not form.is_valid():
        return _modal_error("Invalid form")

    obj = form.save(commit=False)
    obj.customer = customer
    obj.amount = pay_amount
    obj.available = pay_amount
    obj.date = payment_date
    obj.save()

    remainder = pay_amount

    # --- apply payments ---
    for wo in workorders:
        balance = live_open.get(wo.pk, Decimal("0.00"))
        apply_amt = min(balance, remainder).quantize(Decimal("0.01"))

        if apply_amt <= 0:
            continue

        WorkorderPayment.objects.create(
            workorder=wo,
            payment=obj,
            payment_amount=apply_amt,
            date=payment_date,
            void=False,
        )

        recalc_workorder_balances(wo)
        wo.refresh_from_db(fields=["paid_in_full"])

        if wo.paid_in_full:
            Workorder.objects.filter(pk=wo.pk).update(date_paid=payment_date)

        remainder -= apply_amt

    # --- remaining unapplied ---
    obj.available = remainder
    obj.save(update_fields=["available"])

    # --- recompute customer ---
    recompute_customer_open_balance(customer.id)
    recompute_customer_credit(customer.id)

    # --- trigger UI refresh ---
    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = json.dumps({
        "arChanged": True,
        "itemListChanged": True,
    })
    return resp

@login_required
@transaction.atomic
def unrecieve_payment(request):
    paymenttype = PaymentType.objects.all()
    customers = Customer.objects.all().order_by("company_name")

    if request.method == "POST":
        payment_id = request.POST.get("payment_id") or request.POST.get("payment")
        if not (payment_id and str(payment_id).isdigit()):
            return HttpResponse("Missing payment", status=400)

        payment = get_object_or_404(
            Payments.objects.select_for_update(),
            pk=int(payment_id),
            void=False,
        )

        customer_id = payment.customer_id

        # void any applied rows first
        applied_rows = (
            WorkorderPayment.objects
            .select_related("workorder")
            .filter(payment=payment, void=False)
        )

        touched_workorders = set()

        for row in applied_rows:
            WorkorderPayment.objects.filter(pk=row.pk).update(void=True)
            if row.workorder_id:
                touched_workorders.add(row.workorder_id)

        for wo_id in touched_workorders:
            wo = Workorder.objects.select_for_update().get(pk=wo_id)
            recalc_workorder_balances(wo)
            wo.refresh_from_db(fields=["paid_in_full"])
            if not wo.paid_in_full:
                Workorder.objects.filter(pk=wo.pk).update(date_paid=None)

        Payments.objects.filter(pk=payment.pk).update(
            void=True,
            available=Decimal("0.00"),
            void_reason="Unreceived payment",
            voided_at=timezone.now(),
            voided_by=request.user,
        )

        if customer_id:
            recompute_customer_open_balance(customer_id)
            recompute_customer_credit(customer_id)

        return HttpResponse(status=204, headers={"HX-Trigger": "arChanged"})

    form = PaymentForm
    context = {
        "paymenttype": paymenttype,
        "form": form,
        "customers": customers,
    }
    return render(request, "finance/AR/modals/remove_payment.html", context)

@login_required
def payment_detail(request):
    method = ""
    payment_type = None

    payment_type_id = request.GET.get("payment_type")

    if payment_type_id:
        try:
            payment_type = PaymentType.objects.get(pk=payment_type_id)
            method = payment_type.detail_field or ""
        except PaymentType.DoesNotExist:
            pass

    context = {
        "method": method,
        "payment_type": payment_type,
    }

    return render(
        request,
        "finance/AR/partials/payment_detail.html",
        context,
    )


@login_required
@transaction.atomic
def apply_payment(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    payment_id = request.POST.get("payment")
    workorder_id = request.POST.get("workorder")
    raw_amount = (request.POST.get("amount") or "0").strip()
    raw_date = (request.POST.get("date") or "").strip()

    if not (payment_id and payment_id.isdigit() and workorder_id and workorder_id.isdigit()):
        return HttpResponse("Missing fields", status=400)

    try:
        amt = Decimal(raw_amount).quantize(Decimal("0.01"))
    except Exception:
        amt = Decimal("0.00")

    if amt <= Decimal("0.00"):
        return HttpResponse("Amount must be greater than 0", status=400)

    try:
        apply_date = date_cls.fromisoformat(raw_date) if raw_date else timezone.now().date()
    except Exception:
        apply_date = timezone.now().date()

    payment = get_object_or_404(
        Payments.objects.select_for_update().select_related("customer"),
        pk=int(payment_id),
        void=False,
    )
    customer = payment.customer

    workorder = get_object_or_404(
        Workorder.objects.select_for_update(),
        pk=int(workorder_id),
        customer=customer,
        void=False,
    )

    available = Decimal(payment.available or Decimal("0.00")).quantize(Decimal("0.01"))
    if amt > available:
        return HttpResponse("Amount exceeds available payment balance", status=400)

    live = _live_open_balance(workorder)
    if amt > live["open_bal"]:
        return HttpResponse("Amount exceeds workorder open balance", status=400)

    WorkorderPayment.objects.create(
        workorder=workorder,
        payment=payment,
        payment_amount=amt,
        date=apply_date,
        void=False,
    )

    Payments.objects.filter(pk=payment.pk).update(
        available=max(Decimal("0.00"), available - amt)
    )

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=apply_date)

    recompute_customer_open_balance(customer.pk)
    recompute_customer_credit(customer.pk)

    return hx_ar_changed_204()



@login_required
@transaction.atomic
def unapply_payment(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    cust = request.POST.get("customer")
    pk = request.POST.get("workorder_pk")

    if not (cust and str(cust).isdigit() and pk and str(pk).isdigit()):
        return HttpResponse(status=400)

    customer = Customer.objects.select_for_update().get(id=cust)
    workorder = Workorder.objects.select_for_update().get(id=pk)

    applied_rows = (
        WorkorderPayment.objects
        .select_related("payment")
        .filter(workorder_id=pk, void=False)
        .order_by("-id")
    )

    reversed_total = Decimal("0.00")

    for row in applied_rows:
        amt = row.payment_amount or Decimal("0.00")
        if amt <= 0:
            row.void = True
            row.save(update_fields=["void"])
            continue

        if row.payment_id:
            Payments.objects.filter(pk=row.payment_id).update(
                available=Coalesce("available", Value(Decimal("0.00"))) + amt
            )

        row.void = True
        row.save(update_fields=["void"])
        reversed_total += amt

    # Recompute from remaining payment rows instead of forcing unpaid
    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])

    if not workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=None)

    recompute_customer_open_balance(customer.id)
    recompute_customer_credit(customer.id)
    Customer.objects.filter(pk=cust).update(avg_days_to_pay=_recalc_avg_days_to_pay(cust))

    return HttpResponse(status=204, headers={"HX-Trigger": "itemListChanged"})

                

@login_required
@transaction.atomic
def apply_other(request, cust=None):
    customer = cust

    if request.method == "GET":
        form = AppliedElsewhereForm
        context = {
            "form": form,
            "customer": customer,
        }
        return render(request, "finance/AR/modals/apply_elsewhere.html", context)

    customer = request.POST.get("customer")
    amount_raw = (request.POST.get("amount") or "").strip()

    if not (customer and str(customer).isdigit()):
        return HttpResponse("Missing customer", status=400)

    try:
        amount = Decimal(amount_raw).quantize(Decimal("0.01"))
    except Exception:
        amount = Decimal("0.00")

    form = AppliedElsewhereForm(request.POST)

    if amount <= Decimal("0.00"):
        context = {
            "form": form,
            "customer": customer,
            "message": "Please enter an amount greater than 0",
        }
        return render(request, "finance/AR/modals/apply_elsewhere.html", context, status=400)

    if not form.is_valid():
        context = {
            "form": form,
            "customer": customer,
            "message": "Please correct the form errors",
        }
        return render(request, "finance/AR/modals/apply_elsewhere.html", context, status=400)

    cust_obj = Customer.objects.select_for_update().get(id=customer)
    available_credit = Decimal(cust_obj.credit or Decimal("0.00")).quantize(Decimal("0.01"))

    if amount > available_credit:
        context = {
            "form": form,
            "customer": customer,
            "message": "Customer only has credit of:",
            "credit": available_credit,
        }
        return render(request, "finance/AR/modals/apply_elsewhere.html", context, status=400)

    obj = form.save(commit=False)
    obj.customer_id = customer
    obj.amount = amount
    obj.save()

    recompute_customer_credit(cust_obj.id)
    recompute_customer_open_balance(cust_obj.id)

    return redirect("finance:open_invoices", pk=customer)

# @login_required
# def add_bill_payable(request):
#     form = AccountsPayableForm(request.POST or None)
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             if form.is_valid():
#                 obj = form.save(commit=False)
#                 date_due = request.POST.get('date_due')
#                 invoice_date = request.POST.get('invoice_date')
#                 if not date_due:
#                     date = datetime.strptime(invoice_date, "%m/%d/%Y")
#                     #d = timedelta(days=30)
#                     date_due = date + timedelta(days=30)
#                     obj.date_due = date_due
#                 obj.save()
#                 messages.success(request, "Record Added...")
#                 return redirect('finance:add_bill_payable')
#         bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
#         vendors = Vendor.objects.all()
#         context = {
#             'vendors':vendors,
#             'form':form,
#             'bills':bills,
#         }
#         return render(request, 'finance/AP/add_ap.html', context)
#     else:
#         messages.success(request, "You must be logged in")
#         return redirect('home')

@login_required  
def add_daily_sale(request):
    form = DailySalesForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added...")
                return redirect('finance:add_daily_sale')
        return render(request, 'finance/reports/add_daily_sale.html', {'form':form})
    else:
        messages.success(request, "You must be logged in")
        return redirect('home')

@login_required   
def view_daily_sales(request):
    sales_list = DailySales.objects.all()
    return render(request, 'finance/reports/view_sales.html',
        {'sales_list': sales_list})

@login_required
def view_bills_payable(request):
    bills_list = AccountsPayable.objects.all().order_by('-invoice_date')
    return render(request, 'finance/AP/view_bills.html',
        {'bill_list': bills_list})

@login_required
def complete_not_billed(request):
    listing = (
        Workorder.objects
        .filter(completed=True, billed=False, void=False)
        .filter(_q_non_quote())
        .select_related("customer")
        .order_by("hr_customer", "workorder")
    )

    rows = []
    for wo in listing:
        wo.open_balance = _live_total_due(wo)
        rows.append(wo)

    context = {
        "listing": rows,
    }
    return render(request, "finance/reports/complete_not_billed.html", context)


# aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
# #         today = timezone.now()
# #         for x in aging:
# #             if not x.date_billed:
# #                 x.date_billed = today
# #             age = x.date_billed - today
# #             age = abs((age).days)
# #             print(type(age))
# #             Workorder.objects.filter(pk=x.pk).update(aging = age)

@login_required
def ar_aging(request):
    active_ids = Customer.objects.filter(active=True).values_list("id", flat=True)

    workorders = (
        _workorders_base_ar_qs()
        .filter(customer_id__in=active_ids)
        .order_by("hr_customer", "workorder")
    )

    ar, totals = _build_live_aging_rows(workorders, include_billed_today=True)

    context = {
        "total_current": totals["total_current"],
        "total_thirty": totals["total_thirty"],
        "total_sixty": totals["total_sixty"],
        "total_ninety": totals["total_ninety"],
        "total_onetwenty": totals["total_onetwenty"],
        "total_balance": totals["total_balance"],
        "total_billed_today": totals["total_billed_today"],
        "ar": ar,
    }
    return render(request, "finance/reports/ar_aging.html", context)

@login_required
def krueger_ar_aging(request):
    workorders = (
        _workorders_base_ar_qs()
        .filter(internal_company="Krueger Printing")
        .order_by("hr_customer", "printleader_workorder", "workorder")
    )

    ar, totals = _build_live_aging_rows(workorders, include_billed_today=False)

    context = {
        "total_current": totals["total_current"],
        "total_thirty": totals["total_thirty"],
        "total_sixty": totals["total_sixty"],
        "total_ninety": totals["total_ninety"],
        "total_onetwenty": totals["total_onetwenty"],
        "total_balance": totals["total_balance"],
        "ar": ar,
    }
    return render(request, "finance/reports/krueger_ar_aging.html", context)

@login_required
def krueger_ar(request):
    workorders_qs = (
        _workorders_base_ar_qs()
        .filter(internal_company="Krueger Printing")
        .order_by("printleader_workorder", "workorder")
    )

    workorders, total_balance = _build_live_ar_rows(workorders_qs)

    context = {
        "total_balance": total_balance,
        "workorders": workorders,
    }
    return render(request, "finance/reports/krueger_ar.html", context)

@login_required
def lk_ar(request):
    workorders_qs = (
        _workorders_base_ar_qs()
        .exclude(internal_company="Krueger Printing")
        .exclude(internal_company="Office Supplies")
        .order_by("lk_workorder", "workorder")
    )

    workorders, total_balance = _build_live_ar_rows(workorders_qs)

    context = {
        "total_balance": total_balance,
        "workorders": workorders,
    }
    return render(request, "finance/reports/lk_ar.html", context)

@login_required
def all_printleader(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'LK Design').exclude(internal_company = 'Office Supplies').exclude(quote=1).exclude(void=1).order_by('-printleader_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/all_printleader.html', context)

@login_required
def all_open_printleader(request):
    workorders_qs = (
        _workorders_base_ar_qs()
        .exclude(internal_company="LK Design")
        .exclude(internal_company="Office Supplies")
        .order_by("printleader_workorder", "workorder")
    )

    workorders, total_balance = _build_live_ar_rows(workorders_qs)

    context = {
        "total_balance": total_balance,
        "workorders": workorders,
    }
    return render(request, "finance/reports/all_open_printleader.html", context)
@login_required
def all_lk(request):
    workorders = Workorder.objects.filter().exclude(internal_company = 'Krueger Printing').exclude(internal_company = 'Office Supplies').exclude(quote=1).exclude(void=1).order_by('-lk_workorder')
    total_balance = workorders.filter().aggregate(Sum('open_balance'))
    context = {
        'total_balance':total_balance,
        'workorders':workorders,
    }
    return render(request, 'finance/reports/all_lk.html', context)

@login_required
def open_invoices(request, pk, msg=None):
    if msg is None:
        msg = request.GET.get("msg")
    msg = int(msg) if str(msg).isdigit() else None

    workorders_qs = (
        Workorder.objects
        .filter(customer=pk)
        .exclude(billed=0)
        .filter(_q_non_quote())
        .exclude(void=1)
        .exclude(workorder_total=0)
        .order_by("workorder")
    )

    workorders = list(workorders_qs)

    total_open_all = Decimal("0.00")
    filtered = []

    for wo in workorders:
        live = _live_open_balance(wo)
        wo.total_balance_calc = live["total_due"]
        wo.open_balance_calc = live["open_bal"]

        if wo.open_balance_calc > Decimal("0.00"):
            filtered.append(wo)
            total_open_all += wo.open_balance_calc

    payments = (
        Payments.objects
        .filter(customer=pk)
        .exclude(available=None)
        .exclude(void=1)
        .order_by("-date", "-id")
    )

    credits = Customer.objects.get(pk=pk).credit
    message = "Please select a different payment" if msg else ""

    context = {
        "message": message,
        "payments": payments,
        "customer": pk,
        "total_balance": {"open_balance__sum": total_open_all},
        "credit": credits,
        "workorders": filtered,
    }
    return render(request, "finance/reports/modals/open_invoices.html", context)

@login_required
def open_invoices_recieve_payment(request, pk, msg=None):
    if msg is None:
        msg = request.GET.get("msg")
    msg = int(msg) if str(msg).isdigit() else None
    message = "The payment amount is less than the workorders selected" if msg else ""

    customer = Customer.objects.get(id=pk)
    paymenttype = PaymentType.objects.all()
    form = PaymentForm

    base_qs = (
        Workorder.objects
        .filter(customer=pk)
        .exclude(billed=0)
        .filter(_q_non_quote())
        .exclude(void=1)
        .order_by("workorder")
    )
    candidates = list(base_qs)

    workorders = []
    total_open_all = Decimal("0.00")

    for wo in candidates:
        live = _live_open_balance(wo)
        open_bal = live["open_bal"]

        if open_bal <= Decimal("0.00"):
            continue

        wo.total_balance_calc = live["total_due"]
        wo.open_balance_calc = open_bal
        wo.total_balance = live["total_due"]
        wo.open_balance = open_bal

        total_open_all += open_bal
        workorders.append(wo)

    context = {
        "total_balance": {"open_balance__sum": total_open_all},
        "workorders": workorders,
        "paymenttype": paymenttype,
        "customer": customer,
        "form": form,
        "message": message,
    }
    return render(request, "finance/reports/modals/open_invoice_recieve_payment.html", context)

# @login_required
# def payment_history(request):
#     if request.method == "GET":
#         customer = request.GET.get('customer')
#         payment = Payments.objects.filter(customer=customer).exclude(void=1).exclude(available=0).order_by('-date')
#         context = {
#             'payment':payment,
#             'customer':customer,
#         }
#     return render(request, 'finance/AR/partials/payment_history.html', context)

@login_required
@transaction.atomic
def remove_payment(request, pk=None):
    customers = (
        Customer.objects
        .filter()
        .exclude(credit__lte=0)
        .exclude(credit=None)
        .order_by("company_name")
    )

    if request.method == "POST":
        if not pk:
            return HttpResponse(status=400)

        payment = get_object_or_404(
            Payments.objects.select_for_update(),
            pk=pk,
            void=False,
        )

        has_applied = WorkorderPayment.objects.filter(payment=payment, void=False).exists()
        if has_applied:
            return HttpResponse("Cannot remove payment with applied amounts.", status=409)

        customer_id = payment.customer_id

        Payments.objects.filter(pk=payment.pk).update(
            void=True,
            available=Decimal("0.00"),
            void_reason="Removed from AR remove_payment flow",
            voided_at=timezone.now(),
            voided_by=request.user,
        )

        if customer_id:
            recompute_customer_open_balance(customer_id)
            recompute_customer_credit(customer_id)

        return HttpResponse(status=204, headers={"HX-Trigger": "arChanged"})

    context = {
        "customers": customers,
    }
    return render(request, "finance/AR/modals/remove_payment.html", context)



############################################
###########

# AP Invoices

###########
#############################################

@login_required
def add_invoice(request, vendor=None):
    form = AddInvoiceForm()
    vendors = Vendor.objects.all()
    if request.method == "POST":
        form = AddInvoiceForm(request.POST)
        if form.is_valid():
            vendor = request.POST.get('vendor')
            #vendor = Vendor.objects.filter(pk=vendor)
            form.instance.vendor_id = vendor
            form.save()
            invoice = form.instance.pk
            return redirect ('finance:ap_invoice_detail_id', id=invoice)
        else:
            print(form.errors)
        #invoices = RetailInvoices.objects.all().order_by('invoice_date')
        #print(vendor)
        # context = {
        #     'invoices': invoices,
        # }
    #Limit vendors, but this is currently not being used
    #vendors = Vendors.objects.filter(supplier=1)
    if vendor:
        bills = AccountsPayable.objects.filter().order_by('-invoice_date')
        balance = AccountsPayable.objects.filter().exclude(paid=1).exclude(void=True).aggregate(Sum('total'))
        calculated_total = AccountsPayable.objects.filter().exclude(paid=1).exclude(void=True).aggregate(Sum('calculated_total'))
    else:
        bills = AccountsPayable.objects.filter().exclude(vendor=23).order_by('-invoice_date') 
        balance = AccountsPayable.objects.filter().exclude(paid=1).exclude(vendor=23).exclude(void=True).aggregate(Sum('total'))
        calculated_total = AccountsPayable.objects.filter().exclude(paid=1).exclude(vendor=23).exclude(void=True).aggregate(Sum('calculated_total'))  
    context = {
        'balance': balance,
        'calculated_total': calculated_total,
        'form': form,
        'bills':bills,
        'vendors':vendors,
        #'categories': categories
    }
    return render (request, "finance/AP/add_ap.html", context)

def edit_invoice(request, invoice=None, drop=None):
    print('invoice')
    print(invoice)
    pk=invoice
    obj = get_object_or_404(AccountsPayable, id=invoice)
    print(drop)
    if request.method == "POST":
        #instance = AccountsPayable.objects.get(id=pk)
        form = EditInvoiceForm(request.POST or None, instance=obj)
        if form.is_valid():
            inv = form.save(commit=False)
            #InvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
            
            # stamp/unstamp void time
            if inv.void and not inv.voided_at:
                inv.voided_at = timezone.now()
            if not inv.void:
                inv.voided_at = None
                inv.void_reason = ""

            inv.save()
            messages.success(request, "Invoice updated.")

            return redirect ('finance:ap_add_invoice') 
            #return HttpResponse(status=204, headers={'HX-Trigger': 'itemChanged'})         
        else:        
            messages.success(request, "Something went wrong")
            return redirect ('finance:ap_add_invoice')
    
    form = EditInvoiceForm(instance=obj)
    bills = AccountsPayable.objects.filter(pk=invoice).exclude(paid=1).order_by('invoice_date')
    #balance = AccountsPayable.objects.filter().exclude(paid=1).aggregate(Sum('total'))
    #calculated_total = AccountsPayable.objects.filter().exclude(paid=1).aggregate(Sum('calculated_total'))
    vendors = Vendor.objects.all()
    context = {
        #'balance': balance,
        #'calculated_total': calculated_total,
        'vendors':vendors,
        'pk':pk,
        'bills':bills,
        'form':form,
        "invoice_obj": obj,
    }
    return render (request, "finance/AP/edit_invoice.html", context)

def edit_invoice_modal(request, invoice=None):
    pk=invoice
    if request.method == "POST":
        instance = AccountsPayable.objects.get(id=pk)
        form = AddInvoiceForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            #InvoiceItem.objects.filter(pk=id).update(name=name, description=description, vendor_part_number=vendor_part_number, unit_cost=unit_cost, qty=qty)
            return HttpResponse(status=204, headers={'HX-Trigger': 'itemChanged'}) 
            #return redirect ('finance:ap_add_invoice')         
        else:        
            messages.success(request, "Something went wrong")
            return redirect ('finance:ap_add_invoice')
    obj = get_object_or_404(AccountsPayable, id=invoice)
    form = AddInvoiceForm(instance=obj)
    bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
    context = {
        'pk':pk,
        'bills':bills,
        'form':form
    }
    return render (request, "finance/AP/modals/edit_invoice_modal.html", context)




# @login_required
# def add_bill_payable(request):
#     form = AccountsPayableForm(request.POST or None)
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             if form.is_valid():
#                 obj = form.save(commit=False)
#                 date_due = request.POST.get('date_due')
#                 invoice_date = request.POST.get('invoice_date')
#                 if not date_due:
#                     date = datetime.strptime(invoice_date, "%m/%d/%Y")
#                     #d = timedelta(days=30)
#                     date_due = date + timedelta(days=30)
#                     obj.date_due = date_due
#                 obj.save()
#                 messages.success(request, "Record Added...")
#                 return redirect('finance:add_bill_payable')
#         bills = AccountsPayable.objects.filter().exclude(paid=1).order_by('invoice_date')
#         vendors = Vendor.objects.all()
#         context = {
#             'vendors':vendors,
#             'form':form,
#             'bills':bills,
#         }
#         return render(request, 'finance/AP/add_ap.html', context)
#     else:
#         messages.success(request, "You must be logged in")
#         return redirect('home')
    





# make sure these exist where you already had them:
# - AddInvoiceItemForm
# - logger


@login_required
def invoice_detail(request, id=None):
    """
    AP Invoice detail + add/edit line items.

    Shared save path:
    - create/edit line items via finance.services.ap_invoice_items.save_ap_invoice_item_from_post
    - posted flag: HARD LOCK on POST
    """
    from finance.services.ap_invoice_items import save_ap_invoice_item_from_post

    invoice = get_object_or_404(AccountsPayable, id=id)

    # ---- POSTED LOCK (server-side) ----
    if request.method == "POST" and getattr(invoice, "posted", False):
        messages.error(request, "This AP invoice is POSTED and cannot be modified. Unpost it first.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.pk)

    if request.method == "POST":
        edit = request.POST.get("edit")
        invoice_item_pk = request.POST.get("pk")

        instance = None
        if edit == "1" and invoice_item_pk:
            instance = get_object_or_404(InvoiceItem, pk=invoice_item_pk, invoice=invoice)

        result = save_ap_invoice_item_from_post(
            request_post=request.POST,
            invoice=invoice,
            instance=instance,
        )

        form = result["form"]

        if result["ok"]:
            messages.success(request, "Invoice line item saved.")
            response = redirect("finance:ap_invoice_detail_id", id=invoice.pk)
            response["HX-Trigger"] = "itemChanged"
            return response

        messages.error(request, result["error"] or "Please correct the errors below.")

    else:
        form = AddInvoiceItemForm(initial={"vendor": invoice.vendor})

    items = (
        InvoiceItem.objects.filter(invoice=invoice)
        .select_related("internal_part_number", "invoice_unit")
        .order_by("created")
    )

    # Header vs calculated_total mismatch check
    AP_MISMATCH_THRESHOLD = Decimal("1.00")

    def as_decimal(val):
        if val is None:
            return Decimal("0")
        try:
            return Decimal(str(val))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    header_amount = as_decimal(invoice.total)
    item_total = as_decimal(invoice.calculated_total)
    amount_diff = (header_amount - item_total).copy_abs()
    amount_mismatch = amount_diff > AP_MISMATCH_THRESHOLD

    # Audit log entries for this invoice (Admin LogEntry)
    audit_entries = []
    try:
        ct = ContentType.objects.get_for_model(invoice.__class__)
        audit_entries = (
            LogEntry.objects
            .filter(content_type_id=ct.pk, object_id=str(invoice.pk))
            .order_by("-action_time")[:20]
        )
    except Exception:
        logger.exception(f"Failed to load audit LogEntry rows for AP invoice {invoice.pk}")
        audit_entries = []

    context = {
        "invoice": invoice,
        "items": items,
        "form": form,
        "amount_mismatch": amount_mismatch,
        "amount_diff": amount_diff,
        "header_amount": header_amount,
        "item_total": item_total,
        "audit_entries": audit_entries,
    }
    return render(request, "finance/AP/invoice_detail.html", context)


def invoice_detail_highlevel(request, id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)
    vendor = Vendor.objects.get(id=invoice.vendor.id)
    print(vendor)
    print(vendor.id)
    items = InvoiceItem.objects.filter(invoice_id = id)
    context = {
        'vendor':vendor,
        'invoice': invoice,
        'items': items,
    }
    return render(request, 'finance/AP/invoice_detail_highlevel.html', context)


def add_invoice_item(request, invoice=None, vendor=None, type=None):
    measurements = Measurement.objects.order_by("name")

    # Server-side posted lock (HTMX view)
    invoice_obj = get_object_or_404(AccountsPayable, id=invoice)
    blocked = _ap_posted_block(request, invoice_obj, htmx=True)
    if blocked:
        return blocked

    base_unit_name = "Base unit"

    if vendor:
        item_id = request.GET.get("name")
        if item_id:
            try:
                item = get_object_or_404(
                    VendorItemDetail,
                    internal_part_number=item_id,
                    vendor=vendor,
                )

                ipn = item.internal_part_number_id
                variations = (
                    InventoryQtyVariations.objects
                    .filter(inventory_id=ipn)
                    .order_by("variation__name", "variation_qty")
                )

                try:
                    inv = item.internal_part_number
                    if inv and inv.primary_base_unit:
                        base_unit_name = inv.primary_base_unit.name or "Base unit"
                except Exception:
                    base_unit_name = "Base unit"

                primary_base_unit = item.internal_part_number.primary_base_unit
                if not primary_base_unit:
                    primary_base_unit = "No Primary Base Unit"

                context = {
                    "primary_base_unit": primary_base_unit,
                    "base_unit_name": base_unit_name,
                    "variations": variations,
                    "measurements": measurements,
                    "name": item.name,
                    "vpn": item.vendor_part_number,
                    "ipn": ipn,
                    "description": item.description,
                    "vendor": vendor,
                    "invoice": invoice,
                }
                return render(request, "finance/AP/partials/invoice_item_remainder.html", context)

            except Exception:
                # fall back to showing blank remainder form area
                form = AddInvoiceItemForm
                context = {
                    "form": form,
                    "vendor": vendor,
                    "invoice": invoice,
                    "measurements": measurements,
                    "base_unit_name": base_unit_name,
                }
                return render(request, "finance/AP/partials/invoice_item_remainder.html", context)

    # Default: show the picker list of vendor items
    vendor_id = invoice_obj.vendor_id

    if type == 1:
        items = VendorItemDetail.objects.filter(vendor=vendor_id, non_inventory=1)
        title = "Pick a non-inventory item"     
    elif type == 2:
        items = VendorItemDetail.objects.filter(vendor=vendor_id, online_store=1)
        title = "Pick a online store item"
    else:
        items = VendorItemDetail.objects.filter(vendor=vendor_id, non_inventory=0)
        title = "Pick an inventory item"

    form = AddInvoiceItemForm
    context = {
        "title": title,
        "items": items,
        "invoice": invoice,
        "vendor": vendor_id,
        "form": form,
    }
    return render(request, "finance/AP/partials/add_invoice_item.html", context)




def edit_invoice_item(request, invoice=None, id=None):
    item_obj = get_object_or_404(InvoiceItem, id=id)
    pk = item_obj.pk

    invoice_obj = get_object_or_404(AccountsPayable, id=invoice)

    if request.method == "POST":
        blocked = _ap_posted_block(request, invoice_obj, htmx=False)
        if blocked:
            return blocked
    else:
        blocked = _ap_posted_block(request, invoice_obj, htmx=True)
        if blocked:
            return blocked

    if request.method == "POST":
        result = save_ap_invoice_item_from_post(
            request_post=request.POST,
            invoice=invoice_obj,
            instance=item_obj,
        )

        if result["ok"]:
            messages.success(request, "Invoice line item saved.")
        else:
            messages.error(request, result["error"] or "Please correct the errors below.")

        return redirect("finance:ap_invoice_detail_id", id=invoice_obj.id)

    ipn = item_obj.internal_part_number_id
    variations = (
        InventoryQtyVariations.objects
        .filter(inventory_id=ipn)
        .order_by("variation__name", "variation_qty")
    )

    measurements = Measurement.objects.order_by("name")

    base_unit_name = "Base unit"
    try:
        inv = item_obj.internal_part_number
        if inv and inv.primary_base_unit:
            base_unit_name = inv.primary_base_unit.name or "Base unit"
    except Exception:
        base_unit_name = "Base unit"

    selected_variation_id = item_obj.invoice_unit_id
    selected_measurement_id = None
    selected_variation_qty = None
    if item_obj.invoice_unit_id:
        v = item_obj.invoice_unit
        selected_measurement_id = v.variation_id
        selected_variation_qty = v.variation_qty

    context = {
        "variations": variations,
        "measurements": measurements,
        "base_unit_name": base_unit_name,
        "item_obj_ppm": bool(item_obj.ppm),
        "item": InvoiceItem.objects.filter(id=id),
        "name": item_obj.name,
        "vendor": item_obj.vendor_id,
        "vpn": item_obj.vendor_part_number,
        "description": item_obj.description,
        "unit_cost": item_obj.invoice_unit_cost,
        "qty": item_obj.invoice_qty,
        "pk": pk,
        "ipn": ipn,
        "invoice": invoice,
        "selected_variation_id": selected_variation_id,
        "selected_measurement_id": selected_measurement_id,
        "selected_variation_qty": selected_variation_qty,
    }
    return render(request, "finance/AP/partials/edit_invoice_item.html", context)

@login_required
def delete_invoice_item(request, id=None, invoice=None):
    # ---- POSTED LOCK (server-side) ----
    invoice_obj = get_object_or_404(AccountsPayable, id=invoice)
    if getattr(invoice_obj, "posted", False):
        messages.error(request, "This AP invoice is POSTED and cannot be modified. Unpost it first.")
        return redirect("finance:ap_invoice_detail_id", id=invoice_obj.id)
    
    item = get_object_or_404(InvoiceItem, id=id)

    if getattr(item, "ledger_locked", False):
        messages.error(request, "This line has already affected inventory. Delete is blocked; use an adjustment/reversal flow.")
        return redirect("finance:ap_invoice_detail_id", id=invoice)
    
    item_delete = item

    # Capture for ledger reversal
    old_qty = Decimal(item.qty or 0)
    old_item = item.internal_part_number

    vendor = item.vendor.id
    internal_part_number = item.internal_part_number.id

    # Highest price for this vendor + part (before delete)
    items = InvoiceItem.objects.filter(
        vendor=vendor,
        internal_part_number=internal_part_number,
    ).aggregate(Max("unit_cost"))
    price = list(items.values())[0]

    vendorprice = VendorItemDetail.objects.get(
        vendor=vendor,
        internal_part_number=internal_part_number,
    )

    # Lower price for vendor item if highest price was deleted from invoice item
    if price is not None and vendorprice.high_price > price:
        VendorItemDetail.objects.filter(
            vendor=vendor,
            internal_part_number=internal_part_number,
        ).update(high_price=price, updated=datetime.now())

    # Lower price for inventory master if highest price from any vendor was removed
    overall_price = InvoiceItem.objects.filter(
        internal_part_number=internal_part_number
    ).aggregate(Max("unit_cost"))
    op = list(overall_price.values())[0]

    master = InventoryMaster.objects.get(pk=internal_part_number)
    master_price = master.high_price

    if op is not None and master_price > op:
        m = op * 1000
        InventoryMaster.objects.filter(pk=internal_part_number).update(
            high_price=op, unit_cost=op, price_per_m=m, updated=datetime.now()
        )
        try:
            Inventory.objects.filter(internal_part_number=internal_part_number).update(
                unit_cost=op, price_per_m=m, updated=datetime.now()
            )
        except Exception:
            pass

    # Group pricing logic
    groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number)
    high_price_current = 0

    for x in groups:
        group_items = InventoryPricingGroup.objects.filter(group=x.group)
        for x in group_items:
            price_agg = InvoiceItem.objects.filter(
                internal_part_number=x.inventory.id
            ).aggregate(Max("unit_cost"))
            price_val = list(price_agg.values())[0]
            if price_val and price_val > high_price_current:
                high_price_current = price_val

    price = high_price_current
    groups = InventoryPricingGroup.objects.filter(inventory=internal_part_number)
    for x in groups:
        InventoryPricingGroup.objects.filter(group=x.group).update(high_price=price)
        group_items = InventoryPricingGroup.objects.filter(group=x.group)
        for x in group_items:
            y = InventoryMaster.objects.get(pk=x.inventory.id)
            if y.units_per_base_unit:
                cost = price / y.units_per_base_unit
                m = cost * 1000
            else:
                cost = 0
                m = 0

            InventoryMaster.objects.filter(pk=x.inventory.id).update(
                high_price=price,
                unit_cost=cost,
                price_per_m=m,
                updated=datetime.now(),
            )
            VendorItemDetail.objects.filter(
                vendor=vendor, internal_part_number=x.inventory.id
            ).update(high_price=price, updated=datetime.now())
            Inventory.objects.filter(internal_part_number=x.inventory.id).update(
                unit_cost=cost, price_per_m=m, updated=datetime.now()
            )

    # --- NEW: ledger reversal for this item ---
    try:
        if old_item and old_qty:
            record_inventory_movement(
                inventory_item=old_item,
                qty_delta=-old_qty,  # negative = reverse AP_RECEIPT
                source_type="AP_RECEIPT_DELETE",
                source_id=item_delete.id,
                note=f"Delete AP invoice {invoice} item {item_delete.id}",
            )
    except Exception:
        logger.exception(
            f"Failed to record inventory movement on delete for AP invoice item {item_delete.id}"
        )

    # Finally delete the item
    item_delete.delete()

    return redirect("finance:ap_invoice_detail_id", id=invoice)

def add_item_to_vendor(request, vendor=None, invoice=None):
    print('vendor')
    print(vendor)
    print('something')
    if request.method == "POST":
        print('something')
        form = VendorItemDetailForm(request.POST)
        if form.is_valid():
            form.save()
            print('valid')
            invoice = request.POST.get('invoice')
            vendor_part_number = request.POST.get('vendor_part_number')
            vendor = request.POST.get('vendor')
            pk = form.instance.pk
            print(vendor)
            vendor_type = Vendor.objects.get(id=vendor)
            if vendor_type.retail_vendor == 1:
                VendorItemDetail.objects.filter(pk=pk).update(vendor=vendor, vendor_part_number=vendor_part_number)
            return redirect ('finance:invoice_detail', id=invoice)
        else:
            print(form.errors)
    else:
        form = VendorItemDetailForm(initial={"vendor": vendor})
    #Get all inventory items
    items = InventoryMaster.objects.all()
    list = []
    #Go through inventory. If not matched with a vendor, add to select list
    print('lookup1')
    for x in items:
        try:
            #print('lookup1')
            obj = get_object_or_404(VendorItemDetail, internal_part_number=x.pk, vendor=vendor)
            #print(obj)
        except:
            list.append(x)
            #print('except')
            #print(x.pk)
    #print(list)
    context = {
        'form':form,
        'vendor': vendor,
        'invoice': invoice,
        'list':list,
        # 'items':items,
    }
    if not vendor:
        return render (request, "inventory/items/add_item_to_vendor.html", context)
    return render (request, "inventory/partials/add_item_to_vendor.html", context)

def add_inventory_item(request, vendor=None, invoice=None, baseitem=None):
    print(baseitem)
    form = InventoryMasterForm
    if not invoice:
        if request.method == "POST":
            form = InventoryMasterForm(request.POST)
            if form.is_valid():
                #print(form.data)
                print('yippie')
                #vendor = request.POST.get('primary_vendor')
                #form.instance.primary_vendor = vendor
                form.save()
                pk = form.instance.pk
                unit_cost = form.instance.unit_cost
                price_per_m = unit_cost * 1000
                print('Cost per M')
                print(price_per_m)
                InventoryMaster.objects.filter(pk=pk).update(high_price=unit_cost, price_per_m=price_per_m)
                item = InventoryMaster.objects.get(pk=pk)
                primary_unit = item.primary_base_unit.id
                units_per_base = item.units_per_base_unit
                variation = InventoryQtyVariations(inventory=InventoryMaster.objects.get(pk=pk), variation=Measurement.objects.get(id=primary_unit), variation_qty=units_per_base)
                variation.save()
                print(item.pk)
                vendor = item.primary_vendor
                name = item.name
                vpn = item.primary_vendor_part_number
                description = item.description
                supplies = item.supplies
                retail = item.retail
                non_inventory = item.non_inventory
                online_store = item.online_store
                if online_store:
                    print('Online Store')
                    print(online_store)
                print('Online Store Above')
                invoice = request.POST.get('invoice')
                print(vendor)
                item = VendorItemDetail(vendor=vendor, name=name, vendor_part_number=vpn, description=description, supplies=supplies, retail=retail, non_inventory=non_inventory, online_store=online_store, internal_part_number_id=item.pk )
                item.save()
                if online_store:
                    store_item = StoreItemDetails(item=InventoryMaster.objects.get(pk=pk))
                    store_item.save()
                baseitem = request.POST.get('baseitem')
                print(baseitem)
                print('123')
                if baseitem:
                    print('dsajk')
                    messages.success(request, ("Item has been added"))
                    return redirect ('finance:add_inventory_item', baseitem=1)
                    #return redirect ('finance:invoice_detail', id=invoice)
                if invoice is None:
                    return redirect ('finance:invoice_detail', id=invoice)
                #return redirect ('finance:retail_inventory_list')
                return redirect ('finance:invoice_detail', id=invoice)
        context = {
        'form':form,
        'invoice':invoice
        }
        print('test')
        #return redirect ('finance:view_bills_payable')
        if baseitem:
            print(baseitem)
            return render (request, "inventory/items/add_inventory_item.html", context)
        return render (request, "inventory/partials/add_inventory_item.html", context)
    context = {
        'form':form,
        'invoice':invoice
    }
    print(baseitem)
    if baseitem:
        print(baseitem)
        return render (request, "inventory/items/add_inventory_item.html", context)
    print(baseitem)
    return render (request, "inventory/partials/add_inventory_item.html", context)


def vendor_item_remainder(request, vendor=None, invoice=None):
    form = VendorItemDetailForm
    # invoice = invoice
    # vendor = vendor
    item_id = request.GET.get('item')
    print(item_id)
    if item_id:
        try:
            item = get_object_or_404(InventoryMaster, pk=item_id)
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
        return render (request, "inventory/partials/vendor_item_remainder.html", context)


@login_required
def bills_by_vendor(request):
    # Support either param (you had both)
    vendor = request.GET.get("vendor") or request.GET.get("name")

    # Always return the PARTIAL for HTMX swaps
    template = "finance/AP/partials/vendor_bills.html"

    # Guard: invalid/empty prevents 500
    if not (vendor and str(vendor).isdigit()):
        context = {
            "open_bills": [],
            "paid_bills": [],
            "balance": {"total__sum": 0},
            "calculated_total": {"calculated_total__sum": 0},
        }
        return render(request, template, context)

    vendor_id = int(vendor)

    open_bills = (
        AccountsPayable.objects
        .filter(vendor_id=vendor_id)
        .order_by("-invoice_date")
        .exclude(paid=1)
        .exclude(void=True)
    )

    paid_bills = (
        AccountsPayable.objects
        .filter(vendor_id=vendor_id)
        .order_by("-invoice_date")
        .exclude(paid=0)
        .exclude(void=True)
    )

    balance = (
        AccountsPayable.objects
        .filter(vendor_id=vendor_id)
        .exclude(paid=1)
        .exclude(void=True)
        .aggregate(Sum("total"))
    )

    calculated_total = (
        AccountsPayable.objects
        .filter(vendor_id=vendor_id)
        .exclude(paid=1)
        .exclude(void=True)
        .aggregate(Sum("calculated_total"))
    )

    context = {
        "open_bills": open_bills,
        "paid_bills": paid_bills,
        "balance": balance,
        "calculated_total": calculated_total,
    }
    return render(request, template, context)


def bulk_edit_invoices(request, vendor=None):
    if request.method == "POST":
        form = BulkEditInvoiceForm(request.POST)
        if form.is_valid():
            payment = form.instance.payment_method
            check = form.instance.check_number
            if not check:
                check = ''
            vendor = request.POST.get('vendor')
            date = request.POST.get('date')
            date = datetime.strptime(date, '%m/%d/%Y')
            print(date)
            id_list = request.POST.getlist('payment')
            for x in id_list:
                print(x)
                invoice = AccountsPayable.objects.get(pk=x)
                print(invoice.total)
                amount = invoice.total
                AccountsPayable.objects.filter(pk=x).update(paid=True, amount_paid=amount, payment_method=payment, check_number=check, date_paid=date)
            return HttpResponse(status=204, headers={'HX-Trigger': 'WorkorderInfoChanged'})
    invoices = AccountsPayable.objects.filter(vendor=vendor).exclude(paid=1).order_by('-invoice_date')
    form = BulkEditInvoiceForm
    context = {
        'invoices':invoices,
        'form':form,
        'vendor':vendor,
    }
    return render (request, "finance/AP/modals/bulk_edit_invoices.html", context)




@login_required
def payment_history(request):
    year = request.GET.get("year")
    month = request.GET.get("month")

    # Base queryset: real applied payments only, newest first
    qs = (
        WorkorderPayment.objects
        .filter(void=False)
        .exclude(payment__check_number__startswith="LEGACY-RECON-")
        .exclude(payment__refunded_invoice_number="Legacy AR reconciliation")
        .select_related("workorder", "workorder__customer", "payment")
        .order_by("-date")
    )

    today = timezone.now().date()

    # Decide which range to show
    if year and month:
        year = int(year)
        month = int(month)
        start_date = date(year, month, 1)

        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        payments = qs.filter(date__gte=start_date, date__lt=end_date)
        current_range_label = start_date.strftime("%B %Y")
        is_default_range = False
    else:
        start_date = today - timedelta(days=30)
        end_date = today
        payments = qs.filter(date__gte=start_date, date__lte=end_date)
        current_range_label = "Last 30 Days"
        is_default_range = True

    kr_payments = payments.filter(
        workorder__internal_company__in=["Krueger Printing", "Office Supplies"]
    )
    lk_payments = payments.filter(
        workorder__internal_company="LK Design"
    )

    kr_total = kr_payments.aggregate(Sum("payment_amount"))["payment_amount__sum"] or Decimal("0.00")
    lk_total = lk_payments.aggregate(Sum("payment_amount"))["payment_amount__sum"] or Decimal("0.00")

    months = qs.dates("date", "month", order="DESC")

    context = {
        "kr_payments": kr_payments,
        "lk_payments": lk_payments,
        "kr_total": kr_total,
        "lk_total": lk_total,
        "months": months,
        "current_range_label": current_range_label,
        "is_default_range": is_default_range,
    }
    return render(request, "finance/reports/payment_history.html", context)


@login_required
def sales_tax_payable(request):
    """
    Accrual-based sales tax report for Krueger Printing.

    Uses:
      - Workorder.date_billed in the selected range
      - internal_company = 'Krueger Printing'
      - completed = '1'
    """
    form = DateRangeForm(request.POST or None)

    # default context (GET / initial load)
    context = {"form": form}

    if request.method == "POST" and form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        workorders = (
            Workorder.objects
            .filter(
                date_billed__range=(start_date, end_date),
                internal_company="Krueger Printing",
                completed="1",
            )
            .order_by("date_billed")
        )

        # All of these come back as Decimals from the DB; fall back to Decimal(0)
        invoice_subtotal = (
            workorders.aggregate(sum_sub=Sum("subtotal"))["sum_sub"]
            or Decimal("0.00")
        )
        total_tax = (
            workorders.aggregate(sum_tax=Sum("tax"))["sum_tax"]
            or Decimal("0.00")
        )
        invoice_total = (
            workorders.aggregate(sum_total=Sum("workorder_total"))["sum_total"]
            or Decimal("0.00")
        )

        # Taxable vs exempt: same logic you had, just all Decimal-safe
        taxable_workorders = workorders.exclude(tax__isnull=True).exclude(tax=0)
        taxable_total = (
            taxable_workorders.aggregate(sum_total=Sum("workorder_total"))["sum_total"]
            or Decimal("0.00")
        )

        exemptions = invoice_total - taxable_total
        taxable = invoice_subtotal - exemptions

        context.update(
            {
                "form": form,
                "start_date": start_date,
                "end_date": end_date,
                "workorders": workorders,
                "total_tax": total_tax,
                "invoice_total": invoice_total,
                "invoice_subtotoal": invoice_subtotal,  # keep your existing key name
                "exemptions": exemptions,
                "taxable": taxable,
            }
        )

    return render(request, "finance/reports/sales_tax_payable.html", context)

@login_required
def office_supplies_pos_tax(request):
    """
    Accrual-style sales tax report for Office Supplies POS.

    Uses RetailCashSale.created_at date range.
    """
    form = DateRangeForm(request.POST or None)
    context = {"form": form}

    if request.method == "POST" and form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        sales = RetailCashSale.objects.filter(
            created_at__date__range=(start_date, end_date),
            sale__internal_company="Office Supplies",  # adjust if your field differs
        ).select_related("customer", "sale")

        agg = sales.aggregate(
            sum_sub=Sum("subtotal"),
            sum_tax=Sum("tax"),
            sum_total=Sum("total"),
        )

        invoice_subtotal = agg["sum_sub"] or Decimal("0.00")
        total_tax = agg["sum_tax"] or Decimal("0.00")
        invoice_total = agg["sum_total"] or Decimal("0.00")

        # Assume all POS is taxable unless tax=0 on a row
        taxable = invoice_subtotal
        exemptions = invoice_total - taxable  # probably 0, but keeps same structure

        context.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "sales": sales,
                "invoice_total": invoice_total,
                "invoice_subtotoal": invoice_subtotal,  # keep same misspelling for consistency
                "total_tax": total_tax,
                "taxable": taxable,
                "exemptions": exemptions,
            }
        )

    return render(request, "finance/reports/office_supplies_pos_tax.html", context)


def monthly_statements(request):
    statements_dir = os.path.join(settings.MEDIA_ROOT, "statements")
    files = []

    if os.path.exists(statements_dir):
        pdfs = [
            f for f in os.listdir(statements_dir)
            if f.endswith(".pdf")
        ]

        # sort by file modified time, newest first
        pdfs.sort(
            key=lambda f: os.path.getmtime(os.path.join(statements_dir, f)),
            reverse=True
        )

        for f in pdfs:
            files.append({
                "name": f,
                "url": settings.MEDIA_URL + "statements/" + f,
            })

    return render(request, "finance/monthly_statements.html", {"files": files})


@login_required
def sales_comparison_report(request):
    """
    Compare workorder sales between two date ranges, grouped by
    customer + internal_company.

    Features:
    - Filter by date ranges
    - Optional single customer
    - Company checkboxes (one or many)
    - Optional "combine companies" → one row per customer
    - Clickable header sorting (asc/desc) by:
      - customer name
      - period 1 total
      - period 2 total
      - % change
    - CSV export that respects filters & sort
    """

    if request.GET:
        form = SalesComparisonForm(request.GET)
    else:
        form = SalesComparisonForm()

    company_groups = []  # [{company, rows, total_p1, total_p2, total_delta}, ...]
    flat_rows = []
    period1_label = ""
    period2_label = ""

    # current sorting from querystring
    sort = request.GET.get("sort") or "p2"  # default: sort by period2 desc
    direction = request.GET.get("dir") or "desc"
    direction = "asc" if direction == "asc" else "desc"

    if form.is_valid():
        cd = form.cleaned_data
        p1_start = cd["period1_start"]
        p1_end = cd["period1_end"]
        p2_start = cd["period2_start"]
        p2_end = cd["period2_end"]
        customer = cd["customer"]
        companies_selected = cd.get("companies") or []
        combine_companies = cd.get("combine_companies") or False

        period1_label = f"{p1_start.strftime('%Y-%m-%d')} → {p1_end.strftime('%Y-%m-%d')}"
        period2_label = f"{p2_start.strftime('%Y-%m-%d')} → {p2_end.strftime('%Y-%m-%d')}"

        base_filters = {
            "completed": True,
            "void": False,
            "quote": "0",
        }

        p1_start_dt, p1_end_dt = _date_range_to_datetimes(p1_start, p1_end)
        p2_start_dt, p2_end_dt = _date_range_to_datetimes(p2_start, p2_end)

        qs1 = Workorder.objects.filter(
            **base_filters,
            date_billed__gte=p1_start_dt,
            date_billed__lt=p1_end_dt,
        )
        qs2 = Workorder.objects.filter(
            **base_filters,
            date_billed__gte=p2_start_dt,
            date_billed__lt=p2_end_dt,
        )

        if companies_selected:
            qs1 = qs1.filter(internal_company__in=companies_selected)
            qs2 = qs2.filter(internal_company__in=companies_selected)

        if customer:
            qs1 = qs1.filter(customer=customer)
            qs2 = qs2.filter(customer=customer)

        agg1 = (
            qs1.values("customer_id", "customer__company_name", "internal_company")
            .annotate(total=Sum("workorder_total"))
        )
        agg2 = (
            qs2.values("customer_id", "customer__company_name", "internal_company")
            .annotate(total=Sum("workorder_total"))
        )

        def to_decimal(val):
            if val is None:
                return Decimal("0")
            try:
                return Decimal(str(val))
            except Exception:
                return Decimal("0")

        period1_totals = {}
        period2_totals = {}
        customer_names = {}

        for row in agg1:
            key = (row["customer_id"], row["internal_company"])
            period1_totals[key] = to_decimal(row["total"])
            customer_names[row["customer_id"]] = row["customer__company_name"]

        for row in agg2:
            key = (row["customer_id"], row["internal_company"])
            period2_totals[key] = to_decimal(row["total"])
            customer_names[row["customer_id"]] = row["customer__company_name"]

        all_keys = set(period1_totals.keys()) | set(period2_totals.keys())

        rows = []
        for (cust_id, company) in all_keys:
            t1 = period1_totals.get((cust_id, company), Decimal("0"))
            t2 = period2_totals.get((cust_id, company), Decimal("0"))

            if t1 == 0 and t2 == 0:
                continue

            delta = t2 - t1
            pct_change = None
            if t1 != 0:
                pct_change = (delta / t1) * Decimal("100")

            rows.append(
                {
                    "customer_id": cust_id,
                    "customer_name": customer_names.get(cust_id, f"Customer #{cust_id}"),
                    "company": company,
                    "p1_total": t1,
                    "p2_total": t2,
                    "delta": delta,
                    "pct_change": pct_change,
                }
            )

        # Combine companies to one row per customer, if requested
        if combine_companies:
            combined = {}
            for r in rows:
                cid = r["customer_id"]
                if cid not in combined:
                    combined[cid] = {
                        "customer_id": cid,
                        "customer_name": r["customer_name"],
                        "company": "All selected companies",
                        "p1_total": Decimal("0"),
                        "p2_total": Decimal("0"),
                    }
                combined[cid]["p1_total"] += r["p1_total"]
                combined[cid]["p2_total"] += r["p2_total"]

            new_rows = []
            for cid, r in combined.items():
                t1 = r["p1_total"]
                t2 = r["p2_total"]
                delta = t2 - t1
                pct_change = None
                if t1 != 0:
                    pct_change = (delta / t1) * Decimal("100")

                new_rows.append(
                    {
                        "customer_id": cid,
                        "customer_name": r["customer_name"],
                        "company": r["company"],
                        "p1_total": t1,
                        "p2_total": t2,
                        "delta": delta,
                        "pct_change": pct_change,
                    }
                )

            rows = new_rows

        # Sorting helpers
        def sort_key_and_reverse(sort_field, dir_value):
            desc = (dir_value == "desc")

            if sort_field == "p1":
                return (lambda r: r["p1_total"], desc)
            if sort_field == "p2":
                return (lambda r: r["p2_total"], desc)
            if sort_field == "pct":
                # None should go last
                return (
                    lambda r: (
                        r["pct_change"] is None,
                        r["pct_change"] if r["pct_change"] is not None else Decimal("0"),
                    ),
                    desc,
                )
            # default: name
            # for name, default ascending; only reverse if dir=desc
            return (lambda r: r["customer_name"].lower(), desc)

        key_func, reverse_flag = sort_key_and_reverse(sort, direction)

        # Build groups for HTML
        if combine_companies:
            sorted_rows = sorted(rows, key=key_func, reverse=reverse_flag)
            total_p1 = sum(r["p1_total"] for r in sorted_rows)
            total_p2 = sum(r["p2_total"] for r in sorted_rows)
            total_delta = sum(r["delta"] for r in sorted_rows)

            company_groups = [
                {
                    "company": "All selected companies",
                    "rows": sorted_rows,
                    "total_p1": total_p1,
                    "total_p2": total_p2,
                    "total_delta": total_delta,
                }
            ]
        else:
            grouped = defaultdict(list)
            for r in rows:
                grouped[r["company"]].append(r)

            for company, clist in grouped.items():
                sorted_rows = sorted(clist, key=key_func, reverse=reverse_flag)
                total_p1 = sum(r["p1_total"] for r in sorted_rows)
                total_p2 = sum(r["p2_total"] for r in sorted_rows)
                total_delta = sum(r["delta"] for r in sorted_rows)

                company_groups.append(
                    {
                        "company": company,
                        "rows": sorted_rows,
                        "total_p1": total_p1,
                        "total_p2": total_p2,
                        "total_delta": total_delta,
                    }
                )

            company_groups.sort(key=lambda g: g["company"])

        # flat list for CSV (same sort)
        flat_rows = sorted(rows, key=key_func, reverse=reverse_flag)

        # CSV export
        if request.GET.get("export") == "csv":
            filename = "sales_comparison.csv"
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename=\"{filename}\"'

            writer = csv.writer(response)
            writer.writerow(
                [
                    "Company",
                    "Customer",
                    "Period 1 total",
                    "Period 2 total",
                    "Change",
                    "% Change",
                    "Period 1 range",
                    "Period 2 range",
                ]
            )

            for r in flat_rows:
                pct_str = ""
                if r["pct_change"] is not None:
                    pct_str = f"{r['pct_change']:.1f}"

                writer.writerow(
                    [
                        r["company"],
                        r["customer_name"],
                        f"{r['p1_total']:.2f}",
                        f"{r['p2_total']:.2f}",
                        f"{r['delta']:.2f}",
                        pct_str,
                        period1_label,
                        period2_label,
                    ]
                )

            return response

    # Build base querystring without sort/dir/export so headers can add them cleanly
    params_without_sort = request.GET.copy()
    for k in ["sort", "dir", "export"]:
        if k in params_without_sort:
            params_without_sort.pop(k)
    base_qs = params_without_sort.urlencode()

    context = {
        "form": form,
        "company_groups": company_groups,
        "period1_label": period1_label,
        "period2_label": period2_label,
        "current_sort": sort,
        "current_dir": direction,
        "base_qs": base_qs,
    }
    return render(request, "finance/sales_comparison.html", context)

@user_passes_test(lambda u: u.is_staff)
@login_required
def sales_comparison_debug(request):
    """
    Frontend debug view for the sales comparison report.

    Shows counts at each filter step and per internal_company so you can
    see exactly where the data disappears.
    """

    if request.GET:
        form = SalesComparisonForm(request.GET)
    else:
        form = SalesComparisonForm()

    steps = []
    period1_label = ""
    period2_label = ""

    def summarize(label, qs):
        total = qs.count()
        by_company = (
            qs.values("internal_company")
            .annotate(count=Count("id"))
            .order_by("internal_company")
        )
        return {
            "label": label,
            "total": total,
            "by_company": list(by_company),
        }

    # Step 0: all workorders
    qs_all = Workorder.objects.all()
    steps.append(summarize("All workorders (no filters)", qs_all))

    if form.is_valid():
        cd = form.cleaned_data
        p1_start = cd["period1_start"]
        p1_end = cd["period1_end"]
        p2_start = cd["period2_start"]
        p2_end = cd["period2_end"]
        customer = cd["customer"]
        companies_selected = cd.get("companies") or []

        period1_label = f"{p1_start.strftime('%Y-%m-%d')} → {p1_end.strftime('%Y-%m-%d')}"
        period2_label = f"{p2_start.strftime('%Y-%m-%d')} → {p2_end.strftime('%Y-%m-%d')}"

        base_filters = {
            "completed": True,
            "void": False,
            "quote": "0",
        }

        # Step 1: base filters
        qs_base = Workorder.objects.filter(**base_filters)
        steps.append(summarize("Base filters (completed=True, void=False, quote='0')", qs_base))

        # Step 2: base + date_billed not null
        qs_with_billed = qs_base.filter(date_billed__isnull=False)
        steps.append(summarize("Base + date_billed is not null", qs_with_billed))

        p1_start_dt, p1_end_dt = _date_range_to_datetimes(p1_start, p1_end)
        p2_start_dt, p2_end_dt = _date_range_to_datetimes(p2_start, p2_end)

        # Step 3: Period 1 only
        qs_p1 = qs_with_billed.filter(
            date_billed__gte=p1_start_dt,
            date_billed__lt=p1_end_dt,
        )
        steps.append(summarize(f"Period 1 only ({period1_label})", qs_p1))

        # Step 4: Period 2 only
        qs_p2 = qs_with_billed.filter(
            date_billed__gte=p2_start_dt,
            date_billed__lt=p2_end_dt,
        )
        steps.append(summarize(f"Period 2 only ({period2_label})", qs_p2))

        # Step 5: “union” of P1+P2 using Q instead of .union()
        qs_union = qs_with_billed.filter(
            Q(date_billed__gte=p1_start_dt, date_billed__lt=p1_end_dt)
            | Q(date_billed__gte=p2_start_dt, date_billed__lt=p2_end_dt)
        ).distinct()
        steps.append(summarize("Union of Period 1 + Period 2", qs_union))

        # Step 6: company filters
        if companies_selected:
            qs_union_companies = qs_union.filter(internal_company__in=companies_selected)
            steps.append(
                summarize(
                    f"Union + company filter {companies_selected}",
                    qs_union_companies,
                )
            )
        else:
            qs_union_companies = qs_union

        # Step 7: customer filter
        if customer:
            qs_final = qs_union_companies.filter(customer=customer)
            steps.append(
                summarize(
                    f"+ customer filter ({customer})",
                    qs_final,
                )
            )
        else:
            qs_final = qs_union_companies
            steps.append(
                summarize(
                    "Final set (no specific customer selected)",
                    qs_final,
                )
            )

    context = {
        "form": form,
        "steps": steps,
        "period1_label": period1_label,
        "period2_label": period2_label,
    }
    return render(request, "finance/sales_comparison_debug.html", context)


# -------------------------
# UNAPPLY (REVERSE) PAYMENT APPLICATION
# (YOUR LOGIC, kept intact)
# -------------------------
@login_required
@transaction.atomic
def unapply_workorder_payment(request, wop_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    wp = get_object_or_404(
        WorkorderPayment.objects.select_for_update().select_related("workorder", "payment"),
        pk=wop_id,
        void=False,
    )

    workorder = wp.workorder
    payment = wp.payment
    customer_id = getattr(workorder, "customer_id", None)

    amt = Decimal(wp.payment_amount or Decimal("0.00")).quantize(Decimal("0.01"))

    WorkorderPayment.objects.filter(pk=wp.pk).update(void=True)

    if payment_id := getattr(payment, "id", None):
        Payments.objects.filter(pk=payment_id).update(
            available=Coalesce("available", Value(Decimal("0.00"))) + amt
        )

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if not workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=None)

    if customer_id:
        recompute_customer_open_balance(customer_id)
        recompute_customer_credit(customer_id)

    return hx_ar_changed_204()


@login_required
def payment_history_customer(request):
    customer_id = request.GET.get("customer") or request.GET.get("customers")
    if not (customer_id and str(customer_id).isdigit()):
        return render(
            request,
            "finance/AR/partials/payment_history_customer.html",
            {"customer": None, "history": []},
        )

    customer_id = int(customer_id)
    customer = get_object_or_404(Customer, pk=customer_id)

    payments = (
        Payments.objects
        .filter(customer_id=customer_id, void=False)
        .select_related("payment_type")
        .prefetch_related(
            Prefetch(
                "workorderpayment_set",
                queryset=WorkorderPayment.objects.filter(void=False).select_related("workorder"),
            )
        )
        .order_by("-date", "-id")
    )

    wcm_qs = (
        WorkorderCreditMemo.objects
        .filter(void=False, workorder__customer_id=customer_id)
        .select_related("workorder", "credit_memo")
        .order_by("-date", "-id")
    )

    gcr_qs = (
        GiftCertificateRedemption.objects
        .filter(void=False, workorder__customer_id=customer_id)
        .select_related("workorder", "gift_certificate")
        .order_by("-date", "-id")
    )

    history = []

    for p in payments:
        for wp in p.workorderpayment_set.all():
            if not wp.workorder_id or getattr(wp.workorder, "customer_id", None) != customer_id:
                continue

            history.append({
                "date": wp.date,
                "kind": "payment_applied",
                "label": str(p.payment_type),
                "ref": getattr(p, "check_number", None),
                "amount": wp.payment_amount,
                "available": p.available,
                "payment_id": p.id,
                "workorder": wp.workorder,
                "wop_id": wp.id,
            })

        if (p.available or Decimal("0.00")) > Decimal("0.00"):
            history.append({
                "date": p.date,
                "kind": "payment_unapplied",
                "label": str(p.payment_type),
                "ref": getattr(p, "check_number", None),
                "amount": p.amount,
                "available": p.available,
                "payment_id": p.id,
                "workorder": None,
            })

    for wcm in wcm_qs:
        cm = wcm.credit_memo
        history.append({
            "date": wcm.date,
            "kind": "creditmemo_applied",
            "label": f"Credit Memo {cm.memo_number or cm.id}",
            "ref": None,
            "amount": wcm.amount,
            "available": None,
            "workorder": wcm.workorder,
            "wocm_id": wcm.id,
        })

    for r in gcr_qs:
        gc = r.gift_certificate
        history.append({
            "date": r.date,
            "kind": "giftcert_applied",
            "label": f"Gift Cert {gc.certificate_number or gc.id}",
            "ref": None,
            "amount": r.amount,
            "available": None,
            "workorder": r.workorder,
            "gcr_id": r.id,
        })

    history.sort(
        key=lambda x: (
            x["date"],
            x.get("payment_id") or 0,
            x.get("wop_id") or 0,
            x.get("wocm_id") or 0,
            x.get("gcr_id") or 0,
        ),
        reverse=True,
    )

    return render(
        request,
        "finance/AR/partials/payment_history_customer.html",
        {"customer": customer, "history": history},
    )




# -------------------------
# UNAPPLIED / CREDITS PANEL
# -------------------------

@login_required
def unapplied_and_credits_customer(request):
    customer_id = request.GET.get("customer") or request.GET.get("customers")

    if not (customer_id and str(customer_id).isdigit()):
        return render(
            request,
            "finance/AR/partials/unapplied_and_credits_panel.html",
            {
                "customer": None,
                "unapplied": [],
                "credit_memos": [],
                "giftcerts": [],
                "adjustments": [],
                "voided_payments": [],
                "voided_credit_memos": [],
                "voided_giftcerts": [],
            },
        )

    customer = get_object_or_404(Customer, pk=int(customer_id))

    unapplied = (
        Payments.objects
        .filter(customer=customer, void=False)
        .filter(available__gt=0)
        .select_related("payment_type")
        .order_by("-date", "-id")
    )

    credit_memos = (
        CreditMemo.objects
        .filter(customer=customer, void=False)
        .filter(open_balance__gt=0)
        .order_by("-date", "-id")
    )

    giftcerts = (
        GiftCertificate.objects
        .filter(customer=customer, void=False)
        .filter(balance__gt=0)
        .order_by("-issued_date", "-id")
    )

    # ✅ Adjustments (last 25 by default)
    adjustments = (
        CreditAdjustment.objects
        .filter(customer=customer)
        .select_related("created_by", "payment", "credit_memo", "gift_certificate")
        .order_by("-created_at", "-id")[:25]
    )

    # "Voided" panel rows (last 10 each)
    voided_payments = (
        Payments.objects
        .filter(customer=customer, void=True)
        .select_related("payment_type")
        .order_by("-voided_at", "-id")[:10]
    )
    voided_credit_memos = (
        CreditMemo.objects
        .filter(customer=customer, void=True)
        .order_by("-voided_at", "-id")[:10]
    )
    voided_giftcerts = (
        GiftCertificate.objects
        .filter(customer=customer, void=True)
        .order_by("-voided_at", "-id")[:10]
    )

    return render(
        request,
        "finance/AR/partials/unapplied_and_credits_panel.html",
        {
            "customer": customer,
            "unapplied": unapplied,
            "credit_memos": credit_memos,
            "giftcerts": giftcerts,
            "adjustments": adjustments,
            "voided_payments": voided_payments,
            "voided_credit_memos": voided_credit_memos,
            "voided_giftcerts": voided_giftcerts,
        },
    )



# -------------------------
# CREDIT MEMO: MANUAL CREATE
# -------------------------

@login_required
def creditmemo_create(request):
    customer_id = request.GET.get("customer") or request.POST.get("customer")
    customer = (
        get_object_or_404(Customer, pk=int(customer_id))
        if customer_id and str(customer_id).isdigit()
        else None
    )

    if request.method == "GET":
        return render(request, "finance/AR/modals/creditmemo_create.html", {"customer": customer})

    if not customer:
        return HttpResponse("Customer required", status=400)

    amount = Decimal(request.POST.get("amount") or "0")
    if amount <= 0:
        return HttpResponse("Amount must be > 0", status=400)

    desc = (request.POST.get("description") or "").strip() or None
    memo_number = (request.POST.get("memo_number") or "").strip() or None
    date_str = (request.POST.get("date") or "").strip()

    date_val = timezone.now().date()
    if date_str:
        date_val = date_cls.fromisoformat(date_str)

    CreditMemo.objects.create(
        customer=customer,
        date=date_val,
        memo_number=memo_number,
        description=desc,
        amount=amount,
        open_balance=amount,
        void=False,
    )

    return hx_ar_changed_204()


# -------------------------
# PAYMENT -> CREDIT MEMO (AUTO CONVERT AVAILABLE)
# -------------------------

@login_required
@transaction.atomic
def convert_payment_to_creditmemo(request, payment_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    p = get_object_or_404(Payments, pk=payment_id)

    if p.void:
        return HttpResponse(status=409)

    avail = p.available or 0
    if avail <= 0:
        return HttpResponse(status=409)

    CreditMemo.objects.create(
        customer=p.customer,
        date=p.date,
        memo_number=None,
        description=f"Converted from Payment #{p.pk}",
        amount=avail,
        open_balance=avail,
        void=False,
    )

    p.available = 0
    p.save(update_fields=["available"])

    recompute_customer_credit(p.customer_id)

    return HttpResponse(status=204)


# -------------------------
# APPLY / UNAPPLY CREDIT MEMO
# -------------------------

@login_required
def apply_creditmemo_modal(request):
    customer_id = request.GET.get("customer")
    cm_id = request.GET.get("cm")
    if not (customer_id and customer_id.isdigit() and cm_id and cm_id.isdigit()):
        return HttpResponse("Missing customer/cm", status=400)

    customer = get_object_or_404(Customer, pk=int(customer_id))
    credit_memo = get_object_or_404(CreditMemo, pk=int(cm_id), customer=customer, void=False)

    workorders = ar_open_workorders_qs(customer.id)

    return render(request, "finance/AR/modals/apply_creditmemo.html", {
        "customer": customer,
        "credit_memo": credit_memo,
        "workorders": workorders,
        "today": timezone.now().date(),
        "default_date": timezone.now().date(),
    })


@login_required
@transaction.atomic
def apply_creditmemo(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    customer_id = request.POST.get("customer")
    cm_id = request.POST.get("creditmemo")
    wo_id = request.POST.get("workorder")
    raw_amount = (request.POST.get("amount") or "0").strip()
    raw_date = (request.POST.get("date") or "").strip()

    if not (customer_id and customer_id.isdigit() and cm_id and cm_id.isdigit() and wo_id and wo_id.isdigit()):
        return HttpResponse("Missing fields", status=400)

    try:
        amt = Decimal(raw_amount).quantize(Decimal("0.01"))
    except Exception:
        amt = Decimal("0.00")

    if amt <= Decimal("0.00"):
        return HttpResponse("Amount must be > 0", status=400)

    try:
        apply_date = date_cls.fromisoformat(raw_date) if raw_date else timezone.now().date()
    except Exception:
        apply_date = timezone.now().date()

    customer = get_object_or_404(Customer, pk=int(customer_id))
    cm = get_object_or_404(CreditMemo.objects.select_for_update(), pk=int(cm_id), void=False)
    workorder = get_object_or_404(
        Workorder.objects.select_for_update(),
        pk=int(wo_id),
        customer=customer,
        void=False,
    )

    if cm.customer_id and cm.customer_id != customer.id:
        return HttpResponse("Credit memo belongs to a different customer", status=400)

    cm_open = Decimal(cm.open_balance or Decimal("0.00")).quantize(Decimal("0.01"))
    if amt > cm_open:
        return HttpResponse("Amount exceeds credit memo balance", status=400)

    live = _live_open_balance(workorder)
    if amt > live["open_bal"]:
        return HttpResponse("Amount exceeds workorder open balance", status=400)

    WorkorderCreditMemo.objects.create(
        credit_memo=cm,
        workorder=workorder,
        amount=amt,
        date=apply_date,
        void=False,
    )

    CreditMemo.objects.filter(pk=cm.pk).update(
        open_balance=max(Decimal("0.00"), cm_open - amt)
    )

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=apply_date)

    recompute_customer_open_balance(customer.pk)
    recompute_customer_credit(customer.pk)

    return hx_ar_changed_204()


@login_required
@transaction.atomic
def unapply_creditmemo(request, wocm_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    wocm = get_object_or_404(
        WorkorderCreditMemo.objects.select_for_update().select_related("workorder", "credit_memo"),
        pk=wocm_id,
        void=False,
    )

    workorder = wocm.workorder
    cm = wocm.credit_memo
    customer_id = getattr(workorder, "customer_id", None)
    amt = Decimal(wocm.amount or Decimal("0.00")).quantize(Decimal("0.01"))

    WorkorderCreditMemo.objects.filter(pk=wocm.pk).update(void=True)

    if cm:
        cm_open = Decimal(cm.open_balance or Decimal("0.00")).quantize(Decimal("0.01"))
        CreditMemo.objects.filter(pk=cm.pk).update(open_balance=cm_open + amt)

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if not workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=None)

    if customer_id:
        recompute_customer_open_balance(customer_id)
        recompute_customer_credit(customer_id)

    return hx_ar_changed_204()


# -------------------------
# GIFT CERT: MANUAL ISSUE
# -------------------------

@login_required
def giftcertificate_issue(request):
    customer_id = request.GET.get("customer") or request.POST.get("customer")
    customer = (
        get_object_or_404(Customer, pk=int(customer_id))
        if customer_id and str(customer_id).isdigit()
        else None
    )

    if request.method == "GET":
        payment_types = PaymentType.objects.all().order_by("name")

        # PRE-GENERATE next number for display only
        temp_gc = GiftCertificate()
        next_number = temp_gc._generate_certificate_number()

        return render(
            request,
            "finance/AR/modals/giftcertificate_issue.html",
            {
                "customer": customer,
                "payment_types": payment_types,
                "next_number": next_number,
            },
        )

    amt = Decimal(request.POST.get("amount") or "0")
    if amt <= 0:
        return HttpResponse("Amount must be > 0", status=400)

    number = None
    desc = (request.POST.get("description") or "").strip() or None
    date_str = (request.POST.get("issued_date") or "").strip()

    issued_date = timezone.now().date()
    if date_str:
        issued_date = date_cls.fromisoformat(date_str)

    sold_to = (request.POST.get("sold_to") or "").strip() or None
    sold_ref = (request.POST.get("sold_reference") or "").strip() or None

    pt_id = (request.POST.get("sold_payment_type") or "").strip()
    sold_pt = None
    if pt_id and pt_id.isdigit():
        sold_pt = PaymentType.objects.filter(pk=int(pt_id)).first()

    GiftCertificate.objects.create(
        customer=customer,  # may be None
        issued_date=issued_date,
        certificate_number=number,  # will auto-generate in save()
        description=desc,
        original_amount=amt,
        balance=amt,
        void=False,
        sold_to=sold_to,
        sold_reference=sold_ref,
        sold_payment_type=sold_pt,
        sold_at=timezone.now(),
        sold_by=request.user,
    )


    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arChanged"
    return resp


# -------------------------
# APPLY / UNAPPLY GIFT CERT
# -------------------------

@login_required
def apply_giftcert_modal(request):
    customer_id = request.GET.get("customer")
    gc_id = request.GET.get("gc")

    if not (customer_id and customer_id.isdigit() and gc_id and gc_id.isdigit()):
        return HttpResponse("Missing customer/gc", status=400)

    customer = get_object_or_404(Customer, pk=int(customer_id))

    # allow unassigned, but block if assigned to different customer
    giftcert = get_object_or_404(GiftCertificate, pk=int(gc_id), void=False)
    if giftcert.customer_id and giftcert.customer_id != customer.id:
        return HttpResponse("Gift certificate belongs to a different customer", status=400)

    workorders = ar_open_workorders_qs(customer.id)

    return render(request, "finance/AR/modals/apply_giftcert.html", {
        "customer": customer,
        "giftcert": giftcert,
        "workorders": workorders,
        "default_date": timezone.now().date(),
    })


@login_required
@transaction.atomic
def apply_giftcert(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    customer_id = request.POST.get("customer")
    gc_id = request.POST.get("gc")
    wo_id = request.POST.get("workorder")
    raw_amount = (request.POST.get("amount") or "0").strip()
    raw_date = (request.POST.get("date") or "").strip()

    if not (customer_id and customer_id.isdigit() and gc_id and gc_id.isdigit() and wo_id and wo_id.isdigit()):
        return HttpResponse("Missing fields", status=400)

    try:
        amt = Decimal(raw_amount).quantize(Decimal("0.01"))
    except Exception:
        amt = Decimal("0.00")

    if amt <= Decimal("0.00"):
        return HttpResponse("Amount must be > 0", status=400)

    try:
        apply_date = date_cls.fromisoformat(raw_date) if raw_date else timezone.now().date()
    except Exception:
        apply_date = timezone.now().date()

    customer = get_object_or_404(Customer, pk=int(customer_id))
    giftcert = get_object_or_404(GiftCertificate.objects.select_for_update(), pk=int(gc_id), void=False)
    workorder = get_object_or_404(
        Workorder.objects.select_for_update(),
        pk=int(wo_id),
        customer=customer,
        void=False,
    )

    if giftcert.customer_id and giftcert.customer_id != customer.id:
        return HttpResponse("Gift certificate belongs to a different customer", status=400)

    if giftcert.customer_id is None:
        giftcert.customer = customer
        giftcert.save(update_fields=["customer"])

    bal = Decimal(giftcert.balance or Decimal("0.00")).quantize(Decimal("0.01"))
    if amt > bal:
        return HttpResponse("Amount exceeds gift certificate balance", status=400)

    live = _live_open_balance(workorder)
    if amt > live["open_bal"]:
        return HttpResponse("Amount exceeds workorder open balance", status=400)

    GiftCertificateRedemption.objects.create(
        gift_certificate=giftcert,
        workorder=workorder,
        amount=amt,
        date=apply_date,
        void=False,
    )

    GiftCertificate.objects.filter(pk=giftcert.pk).update(balance=bal - amt)

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=apply_date)

    recompute_customer_open_balance(customer.pk)
    recompute_customer_credit(customer.pk)

    return hx_ar_changed_204()


# -------------------------
# APPLY GIFT CERT BY NUMBER (NEW)
# -------------------------

@login_required
def apply_giftcert_by_number_modal(request):
    customer_id = request.GET.get("customer")
    if not (customer_id and customer_id.isdigit()):
        return HttpResponse("Missing customer", status=400)

    customer = get_object_or_404(Customer, pk=int(customer_id))
    workorders = ar_open_workorders_qs(customer.id)

    return render(request, "finance/AR/modals/apply_giftcert_by_number.html", {
        "customer": customer,
        "workorders": workorders,
    })


@login_required
@transaction.atomic
def apply_giftcert_by_number(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    customer_id = request.POST.get("customer")
    wo_id = request.POST.get("workorder")
    number = (request.POST.get("certificate_number") or "").strip()
    raw_amount = (request.POST.get("amount") or "0").strip()
    raw_date = (request.POST.get("date") or "").strip()

    if not (customer_id and customer_id.isdigit() and wo_id and wo_id.isdigit()):
        return HttpResponse("Missing fields", status=400)
    if not number:
        return HttpResponse("Certificate number required", status=400)

    try:
        amt = Decimal(raw_amount).quantize(Decimal("0.01"))
    except Exception:
        amt = Decimal("0.00")

    if amt <= Decimal("0.00"):
        return HttpResponse("Amount must be > 0", status=400)

    try:
        apply_date = date_cls.fromisoformat(raw_date) if raw_date else timezone.now().date()
    except Exception:
        apply_date = timezone.now().date()

    customer = get_object_or_404(Customer, pk=int(customer_id))
    workorder = get_object_or_404(
        Workorder.objects.select_for_update(),
        pk=int(wo_id),
        customer=customer,
        void=False,
    )

    qs = (
        GiftCertificate.objects.select_for_update()
        .filter(void=False)
        .filter(certificate_number__iexact=number)
    )

    count = qs.count()
    if count == 0:
        return HttpResponse("Gift certificate not found", status=404)
    if count > 1:
        return HttpResponse("Multiple gift certificates match that number", status=409)

    giftcert = qs.first()

    if giftcert.customer_id and giftcert.customer_id != customer.id:
        return HttpResponse("Gift certificate belongs to a different customer", status=400)

    if giftcert.customer_id is None:
        giftcert.customer = customer
        giftcert.save(update_fields=["customer"])

    bal = Decimal(giftcert.balance or Decimal("0.00")).quantize(Decimal("0.01"))
    if amt > bal:
        return HttpResponse("Amount exceeds gift certificate balance", status=400)

    live = _live_open_balance(workorder)
    if amt > live["open_bal"]:
        return HttpResponse("Amount exceeds workorder open balance", status=400)

    GiftCertificateRedemption.objects.create(
        gift_certificate=giftcert,
        workorder=workorder,
        amount=amt,
        date=apply_date,
        void=False,
    )

    GiftCertificate.objects.filter(pk=giftcert.pk).update(balance=bal - amt)

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=apply_date)

    recompute_customer_open_balance(customer.pk)
    recompute_customer_credit(customer.pk)

    return hx_ar_changed_204()



@login_required
@transaction.atomic
def unapply_giftcert(request, gcr_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    redemption = get_object_or_404(
        GiftCertificateRedemption.objects.select_for_update().select_related("workorder", "gift_certificate"),
        pk=gcr_id,
        void=False,
    )

    workorder = redemption.workorder
    giftcert = redemption.gift_certificate
    customer_id = getattr(workorder, "customer_id", None)
    amt = Decimal(redemption.amount or Decimal("0.00")).quantize(Decimal("0.01"))

    GiftCertificateRedemption.objects.filter(pk=redemption.pk).update(void=True)

    if giftcert:
        gc_bal = Decimal(giftcert.balance or Decimal("0.00")).quantize(Decimal("0.01"))
        GiftCertificate.objects.filter(pk=giftcert.pk).update(balance=gc_bal + amt)

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if not workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=None)

    if customer_id:
        recompute_customer_open_balance(customer_id)
        recompute_customer_credit(customer_id)

    return hx_ar_changed_204()

@login_required
def ar_action_buttons(request):
    customer_id = request.GET.get("customers") or request.GET.get("customer")
    cid = int(customer_id) if (customer_id and str(customer_id).isdigit()) else None

    return render(
        request,
        "finance/AR/partials/ar_action_buttons.html",
        {"customer_id": cid},
    )

@login_required
@transaction.atomic
def apply_unapplied_payment_modal(request, payment_id):
    payment = get_object_or_404(
        Payments.objects.select_for_update().select_related("customer", "payment_type"),
        pk=payment_id,
        void=False,
    )
    customer = payment.customer

    base_workorders_qs = (
        Workorder.objects
        .filter(customer=customer)
        .filter(completed=True)
        .filter(Q(date_billed__isnull=False) | Q(billed=True))
        .filter(_q_non_quote())
        .exclude(void=True)
        .order_by("workorder")
    )

    # Build modal workorders from live open balances only
    workorders = []
    live_map_all = {}

    for wo in base_workorders_qs:
        live = _live_open_balance(wo)
        live_map_all[wo.pk] = live
        wo.open_balance_calc = live["open_bal"]

        if wo.open_balance_calc > Decimal("0.00"):
            workorders.append(wo)

    if request.method == "GET":
        return render(
            request,
            "finance/AR/modals/apply_unapplied_payment_modal.html",
            {
                "payment": payment,
                "customer": customer,
                "workorders": workorders,
                "default_date": payment.date or timezone.now().date(),
            },
        )

    if request.method != "POST":
        return HttpResponse(status=405)

    selected_ids = request.POST.getlist("workorders")
    selected_ids = [int(x) for x in selected_ids if str(x).isdigit()]

    if not selected_ids:
        return render(
            request,
            "finance/AR/modals/apply_unapplied_payment_modal.html",
            {
                "payment": payment,
                "customer": customer,
                "workorders": workorders,
                "default_date": payment.date or timezone.now().date(),
                "error": "Select at least one workorder.",
            },
            status=400,
        )

    available = Decimal(payment.available or Decimal("0.00")).quantize(Decimal("0.01"))
    if available <= Decimal("0.00"):
        return render(
            request,
            "finance/AR/modals/apply_unapplied_payment_modal.html",
            {
                "payment": payment,
                "customer": customer,
                "workorders": workorders,
                "default_date": payment.date or timezone.now().date(),
                "error": "This payment has no available amount to apply.",
            },
            status=400,
        )

    date_str = (request.POST.get("date") or "").strip()
    applied_date = payment.date or timezone.now().date()
    if date_str:
        try:
            applied_date = timezone.datetime.fromisoformat(date_str).date()
        except Exception:
            pass

    raw_amount = (request.POST.get("amount") or "").strip()
    desired = Decimal("0.00")
    if raw_amount:
        try:
            desired = Decimal(raw_amount).quantize(Decimal("0.01"))
        except Exception:
            desired = Decimal("0.00")

    selected_wos = list(
        Workorder.objects.select_for_update()
        .filter(pk__in=selected_ids, customer_id=customer.id)
        .filter(completed=True)
        .filter(Q(date_billed__isnull=False) | Q(billed=True))
        .filter(_q_non_quote())
        .exclude(void=True)
        .order_by("workorder")
    )

    if not selected_wos:
        return render(
            request,
            "finance/AR/modals/apply_unapplied_payment_modal.html",
            {
                "payment": payment,
                "customer": customer,
                "workorders": workorders,
                "default_date": applied_date,
                "error": "No eligible workorders selected.",
            },
            status=400,
        )

    total_open = Decimal("0.00")
    live_map = {}
    open_selected_wos = []

    for wo in selected_wos:
        live = _live_open_balance(wo)
        live_map[wo.pk] = live

        if live["open_bal"] > Decimal("0.00"):
            open_selected_wos.append(wo)
            total_open += live["open_bal"]

    if not open_selected_wos:
        return render(
            request,
            "finance/AR/modals/apply_unapplied_payment_modal.html",
            {
                "payment": payment,
                "customer": customer,
                "workorders": workorders,
                "default_date": applied_date,
                "error": "Selected workorders are already fully paid.",
            },
            status=400,
        )

    if desired <= Decimal("0.00"):
        desired = min(available, total_open)

    desired = max(Decimal("0.00"), min(desired, available))
    if desired <= Decimal("0.00"):
        return render(
            request,
            "finance/AR/modals/apply_unapplied_payment_modal.html",
            {
                "payment": payment,
                "customer": customer,
                "workorders": workorders,
                "default_date": applied_date,
                "error": "Nothing to apply.",
            },
            status=400,
        )

    remainder = desired

    for wo in open_selected_wos:
        if remainder <= Decimal("0.00"):
            break

        wo_open = live_map[wo.pk]["open_bal"]
        if wo_open <= Decimal("0.00"):
            continue

        apply_amt = min(remainder, wo_open)
        if apply_amt <= Decimal("0.00"):
            continue

        WorkorderPayment.objects.create(
            workorder_id=wo.pk,
            payment_id=payment.pk,
            payment_amount=apply_amt,
            date=applied_date,
            void=False,
        )

        wo_refresh = Workorder.objects.select_for_update().get(pk=wo.pk)
        recalc_workorder_balances(wo_refresh)
        wo_refresh.refresh_from_db(fields=["paid_in_full"])
        if wo_refresh.paid_in_full:
            Workorder.objects.filter(pk=wo.pk).update(date_paid=applied_date)

        remainder -= apply_amt

    applied_total = (
        WorkorderPayment.objects
        .filter(payment_id=payment.pk, void=False)
        .aggregate(total=Sum("payment_amount"))["total"]
        or Decimal("0.00")
    )
    pay_total = Decimal(payment.amount or Decimal("0.00")).quantize(Decimal("0.01"))
    new_available = max(
        Decimal("0.00"),
        pay_total - Decimal(applied_total).quantize(Decimal("0.01")),
    )

    Payments.objects.filter(pk=payment.pk).update(available=new_available)
    recompute_customer_open_balance(customer.id)
    recompute_customer_credit(customer.id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arChanged"
    return resp


def _decimal0(x):
    return x if x is not None else Decimal("0.00")


def _is_orphan_payment(payment: Payments) -> bool:
    """
    Orphan = payment is effectively unusable in AR:
      - void=False (assumed by caller/filter)
      - available == 0 (NULL treated as 0)
      - NOT tied to any workorder:
          - Payments.workorder is NULL
          - AND no non-void WorkorderPayment rows
    """
    if (payment.available or Decimal("0.00")) != Decimal("0.00"):
        return False

    if payment.workorder_id is not None:
        return False

    return not WorkorderPayment.objects.filter(payment=payment, void=False).exists()


@login_required
def orphan_payments_report(request):
    payments = (
        Payments.objects
        .filter(void=False)
        .filter(workorder__isnull=True)                 # legacy FK not set
        .filter(available=Decimal("0.00"))              # ONLY available = 0
        .annotate(
            applied_count=Count(
                "workorderpayment",                     # ORM name (no _set)
                filter=Q(workorderpayment__void=False),
            )
        )
        .filter(applied_count=0)                        # no WO ties
        .select_related("customer", "payment_type")
        .order_by("-date", "-id")
    )

    return render(
        request,
        "finance/AR/reports/orphan_payments_report.html",
        {"payments": payments},
    )


@login_required
@transaction.atomic
def recompute_payment_available(request, payment_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    payment = get_object_or_404(
        Payments.objects.select_for_update(),
        pk=payment_id,
        void=False,
    )

    applied = (
        WorkorderPayment.objects
        .filter(payment=payment, void=False)
        .aggregate(total=models.Sum("payment_amount"))["total"]
        or Decimal("0.00")
    )

    total = payment.amount or Decimal("0.00")
    new_available = max(Decimal("0.00"), total - applied)

    Payments.objects.filter(pk=payment.pk).update(available=new_available)

    # Re-fetch for row rendering
    p = (
        Payments.objects
        .filter(pk=payment.pk)
        .select_related("customer", "payment_type")
        .annotate(
            applied_count=Count(
                "workorderpayment",
                filter=Q(workorderpayment__void=False),
            )
        )
        .first()
    )

    # If it’s no longer orphaned → auto-hide row
    if (
        (p.available or Decimal("0.00")) != Decimal("0.00")
        or p.workorder_id is not None
        or p.applied_count > 0
    ):
        return HttpResponse("", status=200)

    # Still orphan → replace row w/ warning
    return render(
        request,
        "finance/AR/reports/_orphan_payment_row.html",
        {"p": p, "still_orphan": True},
        status=200,
    )



@login_required
@transaction.atomic
def orphan_payment_void(request, payment_id: int):
    """
    Void (soft delete) payment.
    HTMX: remove the row by returning empty 200.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    p = get_object_or_404(Payments.objects.select_for_update(), pk=payment_id, void=False)

    Payments.objects.filter(pk=p.pk).update(void=True)

    # Keep customer AR totals sane
    try:
        recompute_customer_open_balance(p.customer_id)
        recompute_customer_credit(p.customer_id)
    except Exception:
        pass

    return HttpResponse("", status=200)


@login_required
@transaction.atomic
def orphan_payment_force_apply_modal(request, payment_id):
    p = get_object_or_404(
        Payments.objects.select_for_update().select_related("customer", "payment_type"),
        pk=payment_id,
        void=False,
    )

    customer = p.customer
    if customer is None:
        return HttpResponse("Payment has no customer.", status=400)

    workorders = (
        Workorder.objects
        .filter(customer=customer)
        .exclude(billed=False)
        .filter(_q_non_quote())
        .exclude(void=True)
        .order_by("workorder")
    )

    if request.method == "GET":
        return render(
            request,
            "finance/AR/reports/orphan_payment_force_apply_modal.html",
            {
                "payment": p,
                "customer": customer,
                "workorders": workorders,
                "default_date": timezone.now().date(),
            },
        )

    if request.method != "POST":
        return HttpResponse(status=405)

    workorder_id = request.POST.get("workorder")
    raw_amount = (request.POST.get("amount") or "").strip()
    raw_date = (request.POST.get("date") or "").strip()

    if not (workorder_id and workorder_id.isdigit()):
        return render(
            request,
            "finance/AR/reports/orphan_payment_force_apply_modal.html",
            {
                "payment": p,
                "customer": customer,
                "workorders": workorders,
                "default_date": timezone.now().date(),
                "error": "Select a workorder.",
            },
            status=400,
        )

    try:
        amt = Decimal(raw_amount).quantize(Decimal("0.01"))
    except Exception:
        amt = Decimal("0.00")

    if amt <= Decimal("0.00"):
        return render(
            request,
            "finance/AR/reports/orphan_payment_force_apply_modal.html",
            {
                "payment": p,
                "customer": customer,
                "workorders": workorders,
                "default_date": timezone.now().date(),
                "error": "Amount must be greater than 0.00.",
            },
            status=400,
        )

    try:
        applied_date = date_cls.fromisoformat(raw_date) if raw_date else timezone.now().date()
    except Exception:
        applied_date = timezone.now().date()

    workorder = get_object_or_404(
        Workorder.objects.select_for_update(),
        pk=int(workorder_id),
        customer=customer,
        void=False,
    )

    live = _live_open_balance(workorder)
    wo_open = live["open_bal"]
    pay_amt = Decimal(p.available or p.amount or Decimal("0.00")).quantize(Decimal("0.01"))

    amt = min(amt, wo_open, pay_amt)
    if amt <= Decimal("0.00"):
        return render(
            request,
            "finance/AR/reports/orphan_payment_force_apply_modal.html",
            {
                "payment": p,
                "customer": customer,
                "workorders": workorders,
                "default_date": applied_date,
                "error": "Nothing to apply (workorder open balance is 0).",
            },
            status=400,
        )

    WorkorderPayment.objects.create(
        workorder=workorder,
        payment=p,
        payment_amount=amt,
        date=applied_date,
        void=False,
    )

    Payments.objects.filter(pk=p.pk).update(
        workorder=workorder,
        available=max(Decimal("0.00"), pay_amt - amt),
    )

    workorder.refresh_from_db()
    recalc_workorder_balances(workorder)
    workorder.refresh_from_db(fields=["paid_in_full"])
    if workorder.paid_in_full:
        Workorder.objects.filter(pk=workorder.pk).update(date_paid=applied_date)

    recompute_customer_open_balance(customer.id)
    recompute_customer_credit(customer.id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "orphanPaymentsChanged"
    return resp

@login_required
@transaction.atomic
def ar_void_payment(request, payment_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    p = get_object_or_404(
        Payments.objects.select_for_update(),
        pk=payment_id,
        void=False,
    )

    has_applied = WorkorderPayment.objects.filter(payment=p, void=False).exists()
    if has_applied:
        return HttpResponse("Cannot void: payment has applied amounts.", status=409)

    Payments.objects.filter(pk=p.pk).update(
        void=True,
        void_reason="Voided from AR",
        voided_at=timezone.now(),
        voided_by=request.user,
    )

    if p.customer_id:
        recompute_customer_open_balance(p.customer_id)
        recompute_customer_credit(p.customer_id)

    resp = HttpResponse("", status=200)
    resp["HX-Trigger"] = "arChanged"
    return resp

@login_required
@transaction.atomic
def ar_void_credit_memo(request, cm_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    cm = get_object_or_404(
        CreditMemo.objects.select_for_update(),
        pk=cm_id,
        void=False,
    )

    if WorkorderCreditMemo.objects.filter(credit_memo=cm, void=False).exists():
        return HttpResponse("Cannot void: credit memo has applied amounts.", status=409)

    reason = _void_reason(request)
    if not reason:
        return HttpResponse("Reason is required.", status=400)

    CreditMemo.objects.filter(pk=cm.pk).update(
        void=True,
        void_reason=reason,
        voided_at=timezone.now(),
        voided_by=request.user,
    )

    if cm.customer_id:
        recompute_customer_open_balance(cm.customer_id)
        recompute_customer_credit(cm.customer_id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arVoidChanged"
    return resp


@login_required
@transaction.atomic
def ar_void_giftcert(request, gc_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    gc = get_object_or_404(
        GiftCertificate.objects.select_for_update(),
        pk=gc_id,
        void=False,
    )

    if GiftCertificateRedemption.objects.filter(gift_certificate=gc, void=False).exists():
        return HttpResponse("Cannot void: gift certificate has redemptions.", status=409)

    reason = _void_reason(request)
    if not reason:
        return HttpResponse("Reason is required.", status=400)

    GiftCertificate.objects.filter(pk=gc.pk).update(
        void=True,
        void_reason=reason,
        voided_at=timezone.now(),
        voided_by=request.user,
    )

    if gc.customer_id:
        recompute_customer_open_balance(gc.customer_id)
        recompute_customer_credit(gc.customer_id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arVoidChanged"
    return resp

def _void_reason(request) -> str:
    return (request.POST.get("reason") or "").strip()


def _recompute_payment_available(payment: Payments) -> Decimal:
    applied = (
        WorkorderPayment.objects
        .filter(payment=payment, void=False)
        .aggregate(total=models.Sum("payment_amount"))["total"]
        or Decimal("0.00")
    )
    total = payment.amount or Decimal("0.00")
    return max(Decimal("0.00"), total - applied)


@login_required
@transaction.atomic
def ar_void_payment_modal(request, payment_id):
    p = get_object_or_404(Payments.objects.select_for_update().select_related("payment_type"), pk=payment_id)

    # pull non-void applications (what’s blocking void)
    applied_rows = list(
        WorkorderPayment.objects
        .select_related("workorder")
        .filter(payment=p, void=False)
        .order_by("date", "id")
    )

    if request.method == "GET":
        return render(
            request,
            "finance/AR/modals/void_payment_modal.html",
            {"p": p, "applied_rows": applied_rows},
        )

    if request.method != "POST":
        return HttpResponse(status=405)

    # already voided
    if p.void:
        return HttpResponse(status=409)

    action = (request.POST.get("action") or "").strip()

    # ---- CASE A: payment has applied amounts -> offer “remove from invoices” tooling ----
    if applied_rows:
        if action not in {"remove_selected", "remove_all"}:
            # show same modal with an error if someone POSTs without choosing action
            return render(
                request,
                "finance/AR/modals/void_payment_modal.html",
                {"p": p, "applied_rows": applied_rows, "error": "This payment is applied. Choose remove selected or remove all."},
                status=409,
            )

        # decide which WOP ids to remove
        if action == "remove_all":
            to_remove = applied_rows
        else:
            ids = request.POST.getlist("wop_ids")
            ids = [int(x) for x in ids if str(x).isdigit()]
            to_remove = [r for r in applied_rows if r.id in set(ids)]

        if not to_remove:
            return render(
                request,
                "finance/AR/modals/void_payment_modal.html",
                {"p": p, "applied_rows": applied_rows, "error": "Select at least one invoice to remove this payment from."},
                status=400,
            )

        # optional: require a reason for mass removal (recommended)
        reason = (request.POST.get("reason") or "").strip()
        if not reason:
            return render(
                request,
                "finance/AR/modals/void_payment_modal.html",
                {"p": p, "applied_rows": applied_rows, "error": "Reason is required to remove applied payments."},
                status=400,
            )

        # reverse each application (preserve history by voiding rows)
        touched_workorder_ids = set()
        cust_id = None

        for r in to_remove:
            wo = r.workorder
            amt = r.payment_amount or Decimal("0.00")

            # void the application row
            WorkorderPayment.objects.filter(pk=r.pk).update(void=True)

            if wo:
                touched_workorder_ids.add(wo.pk)
                cust_id = wo.customer_id or cust_id

                wo_refresh = Workorder.objects.select_for_update().get(pk=wo.pk)
                recalc_workorder_balances(wo_refresh)

                wo_refresh.refresh_from_db(fields=["paid_in_full"])
                if not wo_refresh.paid_in_full:
                    Workorder.objects.filter(pk=wo.pk).update(date_paid=None)

        # recompute payment availability and clear legacy FK if nothing applied anymore
        new_available = _recompute_payment_available(p)
        remaining_applied = WorkorderPayment.objects.filter(payment=p, void=False).exists()
        if not remaining_applied:
            Payments.objects.filter(pk=p.pk).update(available=new_available, workorder=None)
        else:
            Payments.objects.filter(pk=p.pk).update(available=new_available)

        # recompute customer balances if we touched any WOs
        if cust_id:
            recompute_customer_open_balance(cust_id)
            recompute_customer_credit(cust_id)

        # optional: void payment after removing
        if request.POST.get("also_void") == "1":
            Payments.objects.filter(pk=p.pk).update(
                void=True,
                void_reason=reason,
                voided_at=timezone.now(),
                voided_by=request.user,
            )

        if p.customer_id:
            recompute_customer_open_balance(p.customer_id)
            recompute_customer_credit(p.customer_id)

        resp = HttpResponse(status=204)
        resp["HX-Trigger"] = "arChanged"
        return resp

    # ---- CASE B: no applied amounts -> normal void flow ----
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        return render(
            request,
            "finance/AR/modals/void_payment_modal.html",
            {"p": p, "applied_rows": [], "error": "Reason is required."},
            status=400,
        )

    Payments.objects.filter(pk=p.pk).update(
        void=True,
        void_reason=reason,
        voided_at=timezone.now(),
        voided_by=request.user,
    )

    if p.customer_id:
        recompute_customer_open_balance(p.customer_id)
        recompute_customer_credit(p.customer_id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arChanged"
    return resp


@login_required
@transaction.atomic
def ar_void_creditmemo_modal(request, cm_id):
    cm = get_object_or_404(CreditMemo.objects.select_for_update(), pk=cm_id)

    if cm.void:
        if request.method == "GET":
            return render(request, "finance/AR/modals/void_creditmemo_modal.html", {"cm": cm, "error": "Already voided."})
        return HttpResponse("Already voided.", status=409)

    if request.method == "GET":
        return render(request, "finance/AR/modals/void_creditmemo_modal.html", {"cm": cm})

    if request.method != "POST":
        return HttpResponse(status=405)

    if WorkorderCreditMemo.objects.filter(credit_memo=cm, void=False).exists():
        return render(
            request,
            "finance/AR/modals/void_creditmemo_modal.html",
            {"cm": cm, "error": "Cannot void: credit memo has applied amounts."},
            status=409,
        )

    reason = _void_reason(request)
    if not reason:
        return render(
            request,
            "finance/AR/modals/void_creditmemo_modal.html",
            {"cm": cm, "error": "Reason is required."},
            status=400,
        )

    CreditMemo.objects.filter(pk=cm.pk).update(
        void=True,
        void_reason=reason,
        voided_at=timezone.now(),
        voided_by=request.user,
    )

    if cm.customer_id:
        recompute_customer_open_balance(cm.customer_id)
        recompute_customer_credit(cm.customer_id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arVoidChanged"
    return resp

@login_required
@transaction.atomic
def ar_void_giftcert_modal(request, gc_id):
    gc = get_object_or_404(GiftCertificate.objects.select_for_update(), pk=gc_id)

    if gc.void:
        if request.method == "GET":
            return render(request, "finance/AR/modals/void_giftcert_modal.html", {"gc": gc, "error": "Already voided."})
        return HttpResponse("Already voided.", status=409)

    if request.method == "GET":
        return render(request, "finance/AR/modals/void_giftcert_modal.html", {"gc": gc})

    if request.method != "POST":
        return HttpResponse(status=405)

    if GiftCertificateRedemption.objects.filter(gift_certificate=gc, void=False).exists():
        return render(
            request,
            "finance/AR/modals/void_giftcert_modal.html",
            {"gc": gc, "error": "Cannot void: gift certificate has redemptions."},
            status=409,
        )

    reason = _void_reason(request)
    if not reason:
        return render(
            request,
            "finance/AR/modals/void_giftcert_modal.html",
            {"gc": gc, "error": "Reason is required."},
            status=400,
        )

    GiftCertificate.objects.filter(pk=gc.pk).update(
        void=True,
        void_reason=reason,
        voided_at=timezone.now(),
        voided_by=request.user,
    )

    if gc.customer_id:
        recompute_customer_open_balance(gc.customer_id)
        recompute_customer_credit(gc.customer_id)

    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arVoidChanged"
    return resp
@login_required
def unused_giftcerts_apply_modal(request):
    """
    Shows all UNUSED gift certs that are either:
      - assigned to this customer
      - OR unassigned (customer is NULL)
    Lets user pick ONE gift cert + ONE workorder and apply.
    """
    customer_id = request.GET.get("customer")
    if not (customer_id and customer_id.isdigit()):
        return HttpResponse("Missing customer", status=400)

    customer = get_object_or_404(Customer, pk=int(customer_id))

    workorders = ar_open_workorders_qs(customer.id)

    q = (request.GET.get("q") or "").strip()

    qs = (
        GiftCertificate.objects
        .filter(void=False, balance__gt=0)
        .filter(Q(customer=customer) | Q(customer__isnull=True))
        .order_by("-issued_date", "-id")
    )

    if q:
        qs = qs.filter(
            Q(certificate_number__icontains=q)
            | Q(description__icontains=q)
            | Q(sold_to__icontains=q)
        )

    # keep modal snappy
    giftcerts = list(qs[:200])

    return render(request, "finance/AR/modals/unused_giftcerts_apply.html", {
        "customer": customer,
        "workorders": workorders,
        "giftcerts": giftcerts,
        "default_date": timezone.now().date(),
        "q": q,
    })


@login_required
def customer_full_report(request):
    customer_id = request.GET.get("customer")
    if not (customer_id and customer_id.isdigit()):
        return HttpResponse("Missing customer", status=400)

    customer = get_object_or_404(Customer, pk=int(customer_id))

    # Reuse the SAME history building logic as payment_history_customer
    wop_qs = (
        WorkorderPayment.objects
        .select_related("workorder")
        .filter(void=False)
        .order_by("-date", "-id")
    )

    payments = (
        Payments.objects
        .filter(customer_id=customer.id, void=False)
        .select_related("payment_type")
        .prefetch_related(Prefetch("workorderpayment_set", queryset=wop_qs))
        .order_by("-date", "-id")
    )

    wcm_qs = (
        WorkorderCreditMemo.objects
        .filter(void=False, workorder__customer_id=customer.id)
        .select_related("workorder", "credit_memo")
        .order_by("-date", "-id")
    )

    gcr_qs = (
        GiftCertificateRedemption.objects
        .filter(void=False, workorder__customer_id=customer.id)
        .select_related("workorder", "gift_certificate")
        .order_by("-date", "-id")
    )

    history = []

    for p in payments:
        for wp in p.workorderpayment_set.all():
            if not wp.workorder_id or getattr(wp.workorder, "customer_id", None) != customer.id:
                continue
            history.append({
                "date": wp.date,
                "kind": "payment_applied",
                "label": str(p.payment_type),
                "ref": getattr(p, "check_number", None),
                "amount": wp.payment_amount,
                "available": p.available,
                "workorder": wp.workorder,
            })

        if (p.available or 0) > 0:
            history.append({
                "date": p.date,
                "kind": "payment_unapplied",
                "label": str(p.payment_type),
                "ref": getattr(p, "check_number", None),
                "amount": p.amount,
                "available": p.available,
                "workorder": None,
            })

    for wcm in wcm_qs:
        cm = wcm.credit_memo
        history.append({
            "date": wcm.date,
            "kind": "creditmemo_applied",
            "label": f"Credit Memo {cm.memo_number or cm.id}",
            "ref": None,
            "amount": wcm.amount,
            "available": None,
            "workorder": wcm.workorder,
        })

    for r in gcr_qs:
        gc = r.gift_certificate
        history.append({
            "date": r.date,
            "kind": "giftcert_applied",
            "label": f"Gift Cert {gc.certificate_number or gc.id}",
            "ref": None,
            "amount": r.amount,
            "available": None,
            "workorder": r.workorder,
        })

    history.sort(key=lambda x: x["date"], reverse=True)

    paginator = Paginator(history, 25)
    page = paginator.get_page(request.GET.get("page") or 1)

    return render(request, "finance/AR/reports/customer_full_report.html", {
        "customer": customer,
        "page": page,
    })    

@login_required
def credits_report(request):
    """
    Customers with any credits:
      - Unapplied payments: Payments.available > 0
      - Open credit memos: CreditMemo.open_balance > 0
      - Unused gift certs: GiftCertificate.balance > 0
    """
    # Optional search
    q = (request.GET.get("q") or "").strip()

    # Subquery sums per customer
    pay_sum_sq = (
        Payments.objects
        .filter(customer_id=OuterRef("pk"), void=False, available__gt=0)
        .values("customer_id")
        .annotate(s=Sum("available"))
        .values("s")[:1]
    )

    cm_sum_sq = (
        CreditMemo.objects
        .filter(customer_id=OuterRef("pk"), void=False, open_balance__gt=0)
        .values("customer_id")
        .annotate(s=Sum("open_balance"))
        .values("s")[:1]
    )

    gc_sum_sq = (
        GiftCertificate.objects
        .filter(customer_id=OuterRef("pk"), void=False, balance__gt=0)
        .values("customer_id")
        .annotate(s=Sum("balance"))
        .values("s")[:1]
    )

    qs = (
        Customer.objects
        .annotate(
            unapplied_payments=Coalesce(Subquery(pay_sum_sq, output_field=DecimalField(max_digits=10, decimal_places=2)), Value(Decimal("0.00"))),
            open_credit_memos=Coalesce(Subquery(cm_sum_sq, output_field=DecimalField(max_digits=10, decimal_places=2)), Value(Decimal("0.00"))),
            unused_giftcerts=Coalesce(Subquery(gc_sum_sq, output_field=DecimalField(max_digits=10, decimal_places=2)), Value(Decimal("0.00"))),
        )
        .annotate(total_credits=Coalesce(
            (Coalesce(Subquery(pay_sum_sq, output_field=DecimalField(max_digits=10, decimal_places=2)), Value(Decimal("0.00"))) +
             Coalesce(Subquery(cm_sum_sq, output_field=DecimalField(max_digits=10, decimal_places=2)), Value(Decimal("0.00"))) +
             Coalesce(Subquery(gc_sum_sq, output_field=DecimalField(max_digits=10, decimal_places=2)), Value(Decimal("0.00")))),
            Value(Decimal("0.00"))
        ))
        .filter(
            Q(unapplied_payments__gt=0) | Q(open_credit_memos__gt=0) | Q(unused_giftcerts__gt=0)
        )
        .order_by("company_name", "-total_credits")
    )

    if q:
        qs = qs.filter(Q(company_name__icontains=q) | Q(contact_name__icontains=q))

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page") or 1)

    return render(request, "finance/AR/reports/credits_report.html", {
        "page": page,
        "q": q,
    })


@login_required
def credits_report_customer_modal(request):
    customer_id = request.GET.get("customer")
    if not (customer_id and customer_id.isdigit()):
        return render(request, "finance/AR/modals/credits_report_customer.html", {"error": "Missing customer"})

    customer = get_object_or_404(Customer, pk=int(customer_id))

    payments = (
        Payments.objects
        .filter(customer=customer, void=False, available__gt=0)
        .select_related("payment_type")
        .order_by("-date", "-id")
    )

    credit_memos = (
        CreditMemo.objects
        .filter(customer=customer, void=False, open_balance__gt=0)
        .order_by("-date", "-id")
    )

    giftcerts = (
        GiftCertificate.objects
        .filter(customer=customer, void=False, balance__gt=0)
        .order_by("-issued_date", "-id")
    )

    return render(request, "finance/AR/modals/credits_report_customer.html", {
        "customer": customer,
        "payments": payments,
        "credit_memos": credit_memos,
        "giftcerts": giftcerts,
    })

@login_required
def credits_report_customer_row(request):
    customer_id = request.GET.get("customer")
    if not (customer_id and customer_id.isdigit()):
        return HttpResponse("Missing customer", status=400)

    customer = get_object_or_404(Customer, pk=int(customer_id))

    payments = (
        Payments.objects
        .filter(customer=customer, void=False, available__gt=0)
        .select_related("payment_type")
        .order_by("-date", "-id")
    )

    credit_memos = (
        CreditMemo.objects
        .filter(customer=customer, void=False, open_balance__gt=0)
        .order_by("-date", "-id")
    )

    giftcerts = (
        GiftCertificate.objects
        .filter(customer=customer, void=False, balance__gt=0)
        .order_by("-issued_date", "-id")
    )

    return render(request, "finance/AR/reports/partials/credits_report_customer_row.html", {
        "customer": customer,
        "payments": payments,
        "credit_memos": credit_memos,
        "giftcerts": giftcerts,
    })

@login_required
def adjust_credit_modal(request):
    kind = request.GET.get("kind")
    obj_id = request.GET.get("id")

    if not (kind and obj_id and obj_id.isdigit()):
        return HttpResponse("Missing fields", status=400)

    obj_id = int(obj_id)

    ctx = {"kind": kind}

    if kind == "payment":
        p = get_object_or_404(Payments, pk=obj_id, void=False)
        ctx.update({"customer": p.customer, "payment": p, "available": p.available})
    elif kind == "creditmemo":
        cm = get_object_or_404(CreditMemo, pk=obj_id, void=False)
        ctx.update({"customer": cm.customer, "credit_memo": cm, "available": cm.open_balance})
    elif kind == "giftcert":
        gc = get_object_or_404(GiftCertificate, pk=obj_id, void=False)
        ctx.update({"customer": gc.customer, "giftcert": gc, "available": gc.balance})
    else:
        return HttpResponse("Bad kind", status=400)

    return render(request, "finance/AR/modals/adjust_credit.html", ctx)


@login_required
@transaction.atomic
def adjust_credit(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    kind = request.POST.get("kind")
    obj_id = request.POST.get("id")
    amt = Decimal(request.POST.get("amount") or "0")
    reason = (request.POST.get("reason") or "").strip() or None

    if not (kind and obj_id and obj_id.isdigit()):
        return HttpResponse("Missing fields", status=400)
    if amt <= 0:
        return HttpResponse("Amount must be > 0", status=400)

    obj_id = int(obj_id)

    if kind == "payment":
        p = get_object_or_404(Payments.objects.select_for_update(), pk=obj_id, void=False)
        available = p.available or Decimal("0.00")
        if amt > available:
            return HttpResponse("Amount exceeds available", status=400)

        CreditAdjustment.objects.create(
            kind=CreditAdjustment.KIND_PAYMENT,
            customer=p.customer,
            payment=p,
            amount=amt,
            reason=reason,
            created_by=request.user,
        )
        Payments.objects.filter(pk=p.pk).update(available=available - amt)
        if p.customer_id:
            recompute_customer_credit(p.customer_id)

    elif kind == "creditmemo":
        cm = get_object_or_404(CreditMemo.objects.select_for_update(), pk=obj_id, void=False)
        available = cm.open_balance or Decimal("0.00")
        if amt > available:
            return HttpResponse("Amount exceeds open balance", status=400)

        CreditAdjustment.objects.create(
            kind=CreditAdjustment.KIND_CREDITMEMO,
            customer=cm.customer,
            credit_memo=cm,
            amount=amt,
            reason=reason,
            created_by=request.user,
        )
        CreditMemo.objects.filter(pk=cm.pk).update(open_balance=available - amt)

    elif kind == "giftcert":
        gc = get_object_or_404(GiftCertificate.objects.select_for_update(), pk=obj_id, void=False)
        available = gc.balance or Decimal("0.00")
        if amt > available:
            return HttpResponse("Amount exceeds balance", status=400)

        CreditAdjustment.objects.create(
            kind=CreditAdjustment.KIND_GIFTCERT,
            customer=gc.customer,
            gift_certificate=gc,
            amount=amt,
            reason=reason,
            created_by=request.user,
        )
        GiftCertificate.objects.filter(pk=gc.pk).update(balance=available - amt)

    else:
        return HttpResponse("Bad kind", status=400)

    # refresh any open panels/report rows
    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arChanged"
    return resp



@require_POST
@login_required
def ap_unpost_invoice(request, id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)

    # If it isn't posted, nothing to do
    if not getattr(invoice, "posted", False):
        messages.info(request, "Invoice is already unposted.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, "Unpost reason is required.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    # Unpost
    invoice.posted = False
    invoice.save(update_fields=["posted"])

    # Audit (Django admin log)
    try:
        ct = ContentType.objects.get_for_model(invoice.__class__)
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ct.pk,
            object_id=invoice.pk,
            object_repr=str(invoice),
            action_flag=CHANGE,
            change_message=f"UNPOST AP invoice. Reason: {reason}",
        )
    except Exception:
        # still succeed even if audit write fails
        logger.exception(f"Failed to write admin LogEntry for unpost AP invoice {invoice.pk}")

    messages.success(request, "Invoice unposted.")
    return redirect("finance:ap_invoice_detail_id", id=invoice.id)



@login_required
def ap_post_invoice_modal(request, id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)

    if getattr(invoice, "posted", False):
        return render(
            request,
            "finance/AP/modals/post_invoice_modal.html",
            {"invoice": invoice, "error": "Invoice is already posted."},
        )

    def _as_decimal(val):
        if val is None:
            return Decimal("0")
        try:
            s = str(val).replace("$", "").replace(",", "").strip()
            return Decimal(s) if s else Decimal("0")
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    # Prefer calculated_total; fallback to header total
    expected = _as_decimal(getattr(invoice, "calculated_total", None))
    if expected == Decimal("0"):
        expected = _as_decimal(getattr(invoice, "total", None))

    context = {
        "invoice": invoice,
        "default_amount": expected,
    }
    return render(request, "finance/AP/modals/post_invoice_modal.html", context)

@require_POST
@login_required
def ap_post_invoice(request, id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)

    if getattr(invoice, "posted", False):
        messages.info(request, "Invoice is already posted.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    paid_date_raw = (request.POST.get("paid_date") or "").strip()
    method = (request.POST.get("method") or "").strip()
    ref = (request.POST.get("reference") or "").strip()
    amount_raw = (request.POST.get("amount") or "").strip()
    note = (request.POST.get("note") or "").strip()

    if not paid_date_raw or not method:
        messages.error(request, "Payment date and method are required to post.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    # Parse date: YYYY-MM-DD OR MM/DD/YYYY
    paid_date = None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            paid_date = datetime.strptime(paid_date_raw, fmt).date()
            break
        except ValueError:
            continue
    if paid_date is None:
        messages.error(request, "Invalid payment date. Use YYYY-MM-DD or MM/DD/YYYY.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    def _as_decimal(val):
        if val is None:
            return Decimal("0")
        try:
            s = str(val).replace("$", "").replace(",", "").strip()
            return Decimal(s) if s else Decimal("0")
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    # Expected amount: calculated_total preferred, else header total
    expected = _as_decimal(getattr(invoice, "calculated_total", None))
    if expected == Decimal("0"):
        expected = _as_decimal(getattr(invoice, "total", None))

    amount = _as_decimal(amount_raw)
    if amount <= Decimal("0"):
        messages.error(request, "Amount paid is required.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    # Require note if amount differs (tolerance = 0.01)
    if (amount - expected).copy_abs() > Decimal("0.01") and not note:
        messages.error(request, "Note is required when amount paid differs from invoice total.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

     # Post
    invoice.posted = True
    invoice.date_paid = paid_date
    invoice.amount_paid = amount
    invoice.payment_method = method
    invoice.check_number = ref or ""
    invoice.payment_note = note or ""

    # Mark paid if fully paid, otherwise leave unpaid
    invoice.paid = (amount - expected).copy_abs() <= Decimal("0.01")

    update_fields = [
        "posted",
        "date_paid",
        "amount_paid",
        "payment_method",
        "check_number",
        "payment_note",
        "paid",
    ]
    invoice.save(update_fields=update_fields)

    # Audit log entry includes expected vs paid and the note
    try:
        ct = ContentType.objects.get_for_model(invoice.__class__)
        msg = (
            f"POST AP invoice. Paid date: {paid_date.isoformat()}; Method: {method}"
            f"; Expected: {expected}; Paid: {amount}"
            + (f"; Ref: {ref}" if ref else "")
            + (f"; Note: {note}" if note else "")
        )
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ct.pk,
            object_id=invoice.pk,
            object_repr=str(invoice),
            action_flag=CHANGE,
            change_message=msg,
        )
    except Exception:
        logger.exception(f"Failed to write admin LogEntry for post AP invoice {invoice.pk}")

    messages.success(request, "Invoice posted.")
    return redirect("finance:ap_invoice_detail_id", id=invoice.id)

@login_required
def ap_adjust_invoice_item_modal(request, id=None, item_id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)
    item = get_object_or_404(InvoiceItem, id=item_id, invoice=invoice)

    if getattr(invoice, "posted", False):
        return render(request, "finance/AP/modals/adjust_invoice_item_modal.html", {
            "invoice": invoice,
            "item": item,
            "error": "Invoice is POSTED. Unpost it before adjusting received qty.",
        })

    if not getattr(item, "ledger_locked", False):
        return render(request, "finance/AP/modals/adjust_invoice_item_modal.html", {
            "invoice": invoice,
            "item": item,
            "error": "This line has not affected inventory yet.",
        })
    
    base_unit_name = ""
    try:
        if item.internal_part_number and item.internal_part_number.primary_base_unit:
            base_unit_name = item.internal_part_number.primary_base_unit.name or ""
    except Exception:
        base_unit_name = ""

    return render(request, "finance/AP/modals/adjust_invoice_item_modal.html", {
        "invoice": invoice,
        "item": item,
        "current_qty": item.qty or Decimal("0"),
        "base_unit_name": base_unit_name,
    })


@require_POST
@login_required
def ap_adjust_invoice_item(request, id=None, item_id=None):
    invoice = get_object_or_404(AccountsPayable, id=id)
    item = get_object_or_404(InvoiceItem, id=item_id, invoice=invoice)

    if getattr(invoice, "posted", False):
        messages.error(request, "Invoice is POSTED. Unpost it before adjusting received qty.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    if not getattr(item, "ledger_locked", False):
        messages.error(request, "This line has not affected inventory yet.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    reason = (request.POST.get("reason") or "").strip()
    new_qty_raw = (request.POST.get("new_qty") or "").strip()

    if not reason:
        messages.error(request, "Reason is required.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    try:
        new_qty = Decimal(new_qty_raw.replace(",", ""))
    except Exception:
        messages.error(request, "Invalid quantity.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    if new_qty < 0:
        messages.error(request, "Quantity cannot be negative.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    old_qty = Decimal(item.qty or 0)
    delta = new_qty - old_qty

    if delta == 0:
        messages.info(request, "No change.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    # Write ledger delta
    try:
        record_inventory_movement(
            inventory_item=item.internal_part_number,
            qty_delta=delta,
            source_type="AP_RECEIPT_ADJUST",
            source_id=str(item.id),
            note=f"Adjust received qty on AP invoice {invoice.id} item {item.id}: {reason}",
        )
    except Exception:
        logger.exception(f"Failed to record inventory adjust for AP invoice item {item.id}")
        messages.error(request, "Failed to write inventory adjustment.")
        return redirect("finance:ap_invoice_detail_id", id=invoice.id)

    # Update item qty + recompute invoice_qty to match invoice_unit factor
    factor = Decimal("1")
    try:
        if item.invoice_unit_id and item.invoice_unit and item.invoice_unit.variation_qty:
            factor = Decimal(item.invoice_unit.variation_qty)
    except Exception:
        factor = Decimal("1")

    # invoice_qty is in invoice units; keep it consistent with qty (base)
    if factor == 0:
        factor = Decimal("1")

    new_invoice_qty = (new_qty / factor)

    # Recompute totals
    item.qty = new_qty
    item.invoice_qty = new_invoice_qty
    item.line_total = (Decimal(item.unit_cost or 0) * new_qty)
    item.save(update_fields=["qty", "invoice_qty", "line_total"])

    total = (
        InvoiceItem.objects.filter(invoice=invoice)
        .aggregate(sum_total=Sum("line_total"))["sum_total"]
        or Decimal("0.00")
    )
    invoice.calculated_total = total
    invoice.save(update_fields=["calculated_total"])

    # Audit entry
    try:
        ct = ContentType.objects.get_for_model(invoice.__class__)
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ct.pk,
            object_id=invoice.pk,
            object_repr=str(invoice),
            action_flag=CHANGE,
            change_message=(
                f"ADJUST RECEIVED QTY. Item {item.id} '{item.name}'. "
                f"Old base qty: {old_qty} -> New base qty: {new_qty}. "
                f"Delta: {delta}. Reason: {reason}"
            ),
        )
    except Exception:
        logger.exception(f"Failed to write audit LogEntry for adjust qty AP invoice {invoice.pk}")

    messages.success(request, "Received qty adjusted.")
    return redirect("finance:ap_invoice_detail_id", id=invoice.id)

@staff_member_required
@require_POST
def run_backfill_invoiceitem_ledger_locked(request):

    force = bool(request.POST.get("force"))

    from finance.services.backfills import backfill_invoiceitem_ledger_locked

    try:
        result = backfill_invoiceitem_ledger_locked(force=force)
    except RuntimeError as e:
        messages.error(request, str(e))
        return redirect("controls:special_tools")
    except Exception:
        logger.exception("Backfill failed")
        messages.error(request, "Backfill failed. Check server logs.")
        return redirect("controls:special_tools")

    messages.success(request, f"Backfill complete. Updated {result['updated']} rows.")
    return redirect("controls:special_tools")



#     if request.method == "POST":
#             modal = request.POST.get('modal')
#             id_list = request.POST.getlist('payment')
#             payment_total = 0
#             for x in id_list:
#                 print('payment total')
#                 print(payment_total)
#                 t = Workorder.objects.get(pk=int(x))
#                 balance = t.open_balance
#                 payment_total = payment_total + balance


# @login_required
# def open_invoices_recieve_payment(request, pk, msg=None):
#     if msg:
#        message = "The payment amount is less than the workorders selected"
#     else:
#        message = ''
#     workorders = Workorder.objects.filter(customer=pk).exclude(billed=0).exclude(quote=1).exclude(void=1).order_by('workorder')
#     total_balance = workorders.filter().aggregate(Sum('open_balance'))
#     #total_balance = total_balance.total
#     #print(total_balance)
#     customer = Customer.objects.get(id=pk)
#     #customer = 
#     paymenttype = PaymentType.objects.all()
#     form = PaymentForm

#     context = {
#         'total_balance':total_balance,
#         'workorders':workorders,
#         'paymenttype':paymenttype,
#         'customer':customer,
#         'form': form,
#         'message': message,

#     }
#     return render(request, 'finance/reports/modals/open_invoice_recieve_payment.html', context)





























# def unrecieve_payment(request):
#     paymenttype = PaymentType.objects.all()
#     customers = Customer.objects.all().order_by('company_name')
#     if request.method == "POST":
#             customer = request.POST.get('customer')
#             print(customer)
#             check = request.POST.get('check_number')
#             giftcard = request.POST.get('giftcard_number')
#             refund = request.POST.get('refunded_invoice_number')
#             amount = request.POST.get('amount')
#             amount = int(amount)
#             cust = Customer.objects.get(id=customer)
#             credit = cust.credit - amount
#             Customer.objects.filter(pk=customer).update(credit=credit)
#             return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
#     form = PaymentForm
#     context = {
#         'paymenttype':paymenttype,
#         'form': form,
#         'customers':customers,
#     }
#     return render(request, 'finance/AR/modals/remove_payment.html', context)



















            # obj, created = Araging.objects.update_or_create(
            #     customer_id=x.id,
            #     hr_customer=x.company_name,
            #     date=today,
            #     current=current
            # )
        #current = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer', 'customer_id').annotate(current_balance=Sum('open_balance'))
        #subtotal = WorkorderItem.objects.filter(workorder_id=id).exclude(billable=0).exclude(parent=1).aggregate(Sum('absolute_price'))
        
        #current = customers.filter(customer_id = x.id).aggregate(Sum('open_balance'))
        # current = list(current.values())[0]
        # print(current)
        #print(current.current_bal)
        #print(current.sum)
        #print(open_balance__sum)
        #total.total_with_tax__sum
        #print(current)

    #     total_invoice = WorkorderItem.objects.filter(workorder_id=workorder).exclude(billable=0).aggregate(
    #         sum=Sum('total_with_tax'),
    #         tax=Sum('tax_amount'),
    #         )
    # #total_invoice = list(WorkorderItem.objects.aggregate(Sum('total_with_tax')).values())[0]
    # total = list(total_invoice.values())[0]
    # if not total:
    #     total = 0
    # total = round(total, 2)
    # tax = list(total_invoice.values())[1]

@login_required
def ar_reconcile_legacy_report(request):
    from finance.helpers_ar import q_non_quote, live_open_balance
    from decimal import Decimal

    suspects = []

    qs = (
        Workorder.objects
        .select_related("customer")
        .filter(void=False, paid_in_full=True)
        .filter(q_non_quote())
        .order_by("workorder")
    )

    for wo in qs:
        live = _live_open_balance(wo)
        if live["open_bal"] > Decimal("0.00"):
            suspects.append({
                "id": wo.id,
                "workorder": wo,
                "customer": wo.customer,
                "customer_name": getattr(wo.customer, "company_name", "") if wo.customer else "",
                "legacy_open_balance": wo.open_balance,
                "legacy_amount_paid": wo.amount_paid,
                "live_total_due": live["total_due"],
                "live_total_applied": live["total_applied"],
                "live_open_bal": live["open_bal"],
            })

    context = {
        "suspects": suspects,
        "suspect_count": len(suspects),
    }
    return render(request, "finance/AR/reports/reconcile_legacy_report.html", context)


@login_required
@transaction.atomic
def ar_reconcile_legacy_selected(request):
    from decimal import Decimal
    from django.utils import timezone
    from workorders.services.totals import recalc_workorder_balances

    if request.method != "POST":
        return HttpResponse(status=405)

    ids = request.POST.getlist("workorders")
    ids = [int(x) for x in ids if str(x).isdigit()]

    if not ids:
        messages.error(request, "No workorders selected.")
        return redirect("finance:ar_reconcile_legacy_report")

    # Find a usable fallback payment type for reconciliation rows
    payment_type = (
        PaymentType.objects.filter(name__iexact="Check").first()
        or PaymentType.objects.filter(name__iexact="Cash").first()
        or PaymentType.objects.order_by("id").first()
    )

    if not payment_type:
        messages.error(request, "No Payment Type exists. Create one first, then retry.")
        return redirect("finance:ar_reconcile_legacy_report")

    workorders = (
        Workorder.objects
        .select_for_update()
        .select_related("customer")
        .filter(pk__in=ids)
        .order_by("workorder")
    )

    updated = 0
    skipped = 0

    for wo in workorders:
        live = _live_open_balance(wo)
        missing = (live["total_due"] - live["total_applied"]).quantize(Decimal("0.01"))

        if missing <= Decimal("0.00"):
            skipped += 1
            continue

        payment = Payments.objects.create(
            customer=wo.customer,
            payment_type=payment_type,
            amount=missing,
            available=Decimal("0.00"),
            date=timezone.localdate(),
            check_number=f"LEGACY-RECON-{wo.workorder}",
            refunded_invoice_number="Legacy AR reconciliation",
        )

        WorkorderPayment.objects.create(
            workorder=wo,
            payment=payment,
            payment_amount=missing,
            date=timezone.localdate(),
            void=False,
        )

        recalc_workorder_balances(wo)
        wo.refresh_from_db(fields=["paid_in_full", "date_paid"])

        if wo.paid_in_full and not wo.date_paid:
            Workorder.objects.filter(pk=wo.pk).update(date_paid=timezone.localdate())

        if wo.customer_id:
            recompute_customer_open_balance(wo.customer_id)
            recompute_customer_credit(wo.customer_id)

        updated += 1

    messages.success(
        request,
        f"Reconciled {updated} workorders using payment type '{payment_type}'. Skipped {skipped}."
    )
    return redirect("finance:ar_reconcile_legacy_report")

@login_required
def ar_workorder_quickview(request, workorder_id):
    wo = get_object_or_404(
        Workorder.objects.select_related("customer"),
        pk=workorder_id,
    )

    live = _live_open_balance(wo)
    billed_date = _workorder_billed_date(wo)
    paid_date = getattr(wo, "date_paid", None)

    if billed_date:
        aging_days = _workorder_aging_days(wo, today_date=timezone.localdate())
    else:
        aging_days = 0

    days_to_pay = None
    if billed_date and paid_date:
        pd = paid_date.date() if hasattr(paid_date, "date") else paid_date
        days_to_pay = max((pd - billed_date).days, 0)

    context = {
        "wo": wo,
        "live": live,
        "billed_date": billed_date,
        "paid_date": paid_date,
        "aging_days": aging_days,
        "days_to_pay": days_to_pay,
    }
    return render(request, "finance/AR/modals/workorder_quickview.html", context)

@login_required
def ar_slow_payers_report(request):
    today_date = timezone.localdate()

    closed_qs = (
        Workorder.objects
        .select_related("customer")
        .filter(billed=True)
        .exclude(void=True)
        .filter(_q_non_quote())
        .order_by("customer_id", "-workorder")
    )

    customer_stats = {}

    for wo in closed_qs:
        live = _live_open_balance(wo)
        if live["total_due"] <= Decimal("0.00"):
            continue
        if live["open_bal"] != Decimal("0.00"):
            continue

        billed_date = _workorder_billed_date(wo)
        paid_date = getattr(wo, "date_paid", None)
        if not billed_date or not paid_date:
            continue

        if hasattr(paid_date, "date"):
            paid_date = paid_date.date()

        days_to_pay = max((paid_date - billed_date).days, 0)

        customer_id = wo.customer_id
        customer_name = (
            getattr(wo.customer, "company_name", None)
            or wo.hr_customer
            or f"Customer {customer_id}"
        )

        row = customer_stats.setdefault(customer_id, {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "closed_count": 0,
            "total_billed": Decimal("0.00"),
            "total_days": 0,
            "avg_days_to_pay": None,
            "max_days_to_pay": 0,
        })

        row["closed_count"] += 1
        row["total_billed"] += live["total_due"]
        row["total_days"] += days_to_pay
        row["max_days_to_pay"] = max(row["max_days_to_pay"], days_to_pay)

    rows = []
    for row in customer_stats.values():
        if row["closed_count"]:
            row["avg_days_to_pay"] = round(row["total_days"] / row["closed_count"], 1)
            rows.append(row)

    rows.sort(key=lambda x: (-x["avg_days_to_pay"], x["customer_name"].lower()))

    context = {
        "rows": rows,
        "generated_on": today_date,
    }
    return render(request, "finance/AR/reports/slow_payers_report.html", context)

@login_required
@require_POST
def krueger_bulk_statements_start(request):
    """
    Starts async build for one merged Krueger bulk statement PDF.
    """
    companies = request.POST.getlist("companies")
    customer_id = request.POST.get("customer") or None

    # default behavior from your existing logic:
    # exclude LK Design unless explicitly chosen
    filters_json = {
        "companies": companies,
        "customer_id": customer_id,
    }

    run = StatementRun.objects.create(
        report_type="krueger_bulk",
        status="pending",
        requested_by=request.user,
        filters_json=filters_json,
    )

    build_krueger_bulk_statements.delay(run.pk)

    return render(
        request,
        "finance/partials/krueger_bulk_statement_run_status.html",
        {"run": run},
    )


@login_required
@require_GET
def krueger_bulk_statements_status(request, run_id):
    run = get_object_or_404(StatementRun, pk=run_id)
    return render(
        request,
        "finance/partials/krueger_bulk_statement_run_status.html",
        {"run": run},
    )


@login_required
@require_GET
def krueger_bulk_statements_download(request, run_id):
    run = get_object_or_404(StatementRun, pk=run_id)

    if run.status != "complete" or not run.file:
        raise Http404("Report is not ready.")

    response = FileResponse(run.file.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{run.file.name.rsplit("/", 1)[-1]}"'
    return response





    




















# def ar_aging(request):
#     customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     current = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer').annotate(current_balance=Sum('open_balance'))
#     thirty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).values('hr_customer').annotate(thirty=Sum('open_balance'))
#     sixty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).values('hr_customer').annotate(sixty=Sum('open_balance'))
#     ninety = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).values('hr_customer').annotate(ninety=Sum('open_balance'))
#     onetwenty = customers.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).values('hr_customer').annotate(onetwenty=Sum('open_balance'))
#     total = customers.all().values('hr_customer').annotate(total_balance=Sum('open_balance'))

#     #total_balance = Workorder.objects.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
#     total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0

#     # Aggregate individual balances for each customer
#     individual_balances = Workorder.objects.values('hr_customer').annotate(
#         #total_balance=Sum('open_balance'),
#         total_balance=Subquery(total.filter(hr_customer=models.OuterRef('hr_customer')).values('total_balance')[:1]),
#         current=Subquery(current.filter(hr_customer=models.OuterRef('hr_customer')).values('current_balance')[:1]),
#         #current=Subquery(current),
#         thirty=Subquery(thirty.filter(hr_customer=models.OuterRef('hr_customer')).values('thirty')[:1]),
#         sixty=Subquery(sixty.filter(hr_customer=models.OuterRef('hr_customer')).values('sixty')[:1]),
#         ninety=Subquery(ninety.filter(hr_customer=models.OuterRef('hr_customer')).values('ninety')[:1]),
#         onetwenty=Subquery(onetwenty.filter(hr_customer=models.OuterRef('hr_customer')).values('onetwenty')[:1]),
#         ).order_by('hr_customer')
    
#     for x in individual_balances:
#         print(x)

#     context = {
#             'customers':customers,
#             'total_balance':total_balance,
#             'individual_balances':individual_balances,
#         }
#     return render(request, 'finance/reports/ar_aging.html', context)








# def ar_aging(request):
#     #balance = Workorder.objects.all.exclude(quote=1).aggregate(Sum('total_balance'))
#     customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)

#     # #aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
#     # today = timezone.now()
#     # for x in customers:
#     #     if not x.date_billed:
#     #         x.date_billed = today
#     #     age = x.date_billed - today
#     #     age = abs((age).days)
#     #     print(x.hr_customer)
#     #     print(type(age))
#     #     print(age)
#     #     #Workorder.objects.filter(pk=x.pk).update(aging = age)










#     current = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).values('hr_customer').annotate(current_balance=Sum('open_balance'))
#     thirty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).values('customer_id').annotate(thirty=Sum('open_balance'))
#     sixty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).values('customer_id').annotate(sixty=Sum('open_balance'))
#     ninety = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).values('customer_id').annotate(ninety=Sum('open_balance'))
#     onetwenty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).values('customer_id').annotate(onetwenty=Sum('open_balance'))
#     total = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).values('customer_id').annotate(current_balance=Sum('open_balance'))
#     #cust = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     #balance = sum(customers.open_balance for customer in customers)

#     # print(list(current))
#     # for x in current:
#          #print(x.hr_customer)
#          #print(x.current_balance)
#         #print(x)
#     # Calculate the total balance
#     #total_balance = Workorder.objects.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
#     total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0
        

#     # Aggregate individual balances for each customer
#     #individual_balances = Workorder.objects.values('hr_customer').annotate(total_balance=Sum('open_balance'))
#     #individual_balances = customers.values('hr_customer').annotate(total_balance=Sum('open_balance'), current=Subquery(current))
#     individual_balances = Workorder.objects.values('hr_customer').annotate(
#         total_balance=Sum('open_balance'),
#         # total_balance=Sum(
#         #     Case(
#         #         When(
#         #             billed = 0, # Exclude Workorders where billed is 0
#         #             paid_in_full = 1,
#         #             quote = 1,
#         #             then='open_balance',
#         #         ),
#         #         default=Value(0),
#         #         output_field=DecimalField(),
#         #     ),
#         # ),
#         #total_balance = Subquery(total.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')[:1]),
#         current=Subquery(current.filter(hr_customer=OuterRef('hr_customer')).values('open_balance')),
#         thirty=Subquery(thirty.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         sixty=Subquery(sixty.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         ninety=Subquery(ninety.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         onetwenty=Subquery(onetwenty.filter(hr_customer=models.OuterRef('hr_customer')).values('open_balance')),
#         )
    
#     for x in individual_balances:
#         print(x)
    
#     # for x in individual_balances:
#     #     print(individual_balances)

#     context = {
#             'customers':customers,
#             'total_balance':total_balance,
#             'individual_balances':individual_balances,
#         }
#     return render(request, 'finance/reports/ar_aging.html', context)









# def ar_aging(request):
#     customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     current = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29)
#     thirty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59)
#     sixty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89)
#     ninety = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119)
#     onetwenty = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120)

#     # Calculate the total balance
#     total_balance = customers.aggregate(total_balance=Sum('open_balance'))['total_balance'] or 0

#     # Aggregate individual balances for each customer
#     individual_balances = customers.values('hr_customer').annotate(total_balance=Sum('open_balance'))

#     context = {
#             'customers':customers,
#             'total_balance':total_balance,
#             'individual_balances':individual_balances,
#         }
#     return render(request, 'finance/reports/ar_aging.html', context)







# @login_required
# def expanded_detail(request, id=None):
#     if not id:
#         id = request.GET.get('customers')
#         search = 0
#     else:
#         search = 1
#     customers = Customer.objects.all()
#     print(id)
#     if id:
#         aging = Workorder.objects.all().exclude(billed=0).exclude(paid_in_full=1)
#         today = timezone.now()
#         for x in aging:
#             if not x.date_billed:
#                 x.date_billed = today
#             age = x.date_billed - today
#             age = abs((age).days)
#             print(type(age))
#             Workorder.objects.filter(pk=x.pk).update(aging = age)
        
#         customer = Customer.objects.get(id=id)
#         cust = customer.id
#         history = Workorder.objects.filter(customer_id=customer).exclude(workorder=id).order_by("-workorder")[:5]
#         workorder = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=1).exclude(quote=1).order_by("-workorder")[:25]
#         completed = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
#         quote = Workorder.objects.filter(customer_id=customer).exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
#         balance = Workorder.objects.filter(customer_id=customer).exclude(quote=1).aggregate(Sum('total_balance'))
#         current = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
#         thirty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lte = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
#         sixty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
#         ninety = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
#         onetwenty = Workorder.objects.filter(customer_id=customer).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
#         #current = list(current.values())[0]
#         #current = round(current, 2)


#         context = {
#             'workorders': workorder,
#             'completed': completed,
#             'quote': quote,
#             'cust': cust,
#             'customers':customers,
#             'customer': customer,
#             'history': history,
#             'balance': balance,
#             'current':current,
#             'thirty':thirty,
#             'sixty':sixty,
#             'ninety':ninety,
#             'onetwenty':onetwenty,
#         }
#         if search:
#             return render(request, "customers/search_detail.html", context)
#         else:
#             return render(request, "customers/partials/details.html", context)














    #         else:
    #             credit = workorder.total_balance















    #         total = workorder.total_balance
    #         date = timezone.now()
    #         credit = customer.credit
    #         if partial:
    #             partial = int(partial)
    #             if credit > partial:
    #                 open = workorder.open_balance
    #                 paid = workorder.amount_paid
    #                 if paid:
    #                     paid = paid + partial
    #                 else:
    #                     paid = partial
    #                 if paid > total:
    #                     partial = open
    #                     paid = total
    #                 open = open - partial
    #                 credit = credit - partial
    #                 Workorder.objects.filter(pk=pk).update(open_balance = open, amount_paid = paid, date_paid = date)
    #                 Customer.objects.filter(pk=cust).update(credit = credit)
    #                 return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    #             else:
    #                 return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})
    #         else:
    #             open = workorder.open_balance   
    #         if credit > open:
    #             Workorder.objects.filter(pk=pk).update(open_balance = 0, amount_paid = total, date_paid = date)
    #             credit = credit - open
    #             Customer.objects.filter(pk=cust).update(credit = credit)
    # return HttpResponse(status=204, headers={'HX-Trigger': 'itemListChanged'})