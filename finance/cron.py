from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, Max, Count, Min, Sum, Subquery, Case, When, Value, DecimalField, OuterRef
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import logging
from django.db import transaction
from .models import AccountsPayable, DailySales, Araging, Payments, WorkorderPayment, Krueger_Araging
from .forms import AccountsPayableForm, DailySalesForm, AppliedElsewhereForm, PaymentForm
from retail.forms import RetailInventoryMasterForm
from finance.forms import AddInvoiceForm, AddInvoiceItemForm, EditInvoiceForm
from finance.models import InvoiceItem, ArSlowPayerSnapshotRun, ArSlowPayerSnapshot, WorkorderPayment
from customers.models import Customer
from workorders.models import Workorder
from controls.models import PaymentType, Measurement
from inventory.models import Vendor, InventoryMaster, VendorItemDetail, InventoryQtyVariations, InventoryPricingGroup, Inventory
from inventory.forms import InventoryMasterForm, VendorItemDetailForm
from onlinestore.models import StoreItemDetails
from finance.helpers_ar import live_open_balance

def _get_paid_date(workorder):
    """
    Resolve a real paid date for cron (no annotations available).
    """
    # If you have a real field, use it
    if hasattr(workorder, "date_paid") and workorder.date_paid:
        return workorder.date_paid

    # fallback: latest applied payment
    payment = (
        WorkorderPayment.objects
        .filter(workorder=workorder, void=False)
        .order_by("-payment__date")
        .select_related("payment")
        .first()
    )

    if payment and payment.payment and payment.payment.date:
        return payment.payment.date

    return None

def ar_aging():
    today = timezone.now()
    today_date = today.date()

    customers = Customer.objects.all()
    workorders = (
        Workorder.objects.filter()
        .exclude(billed=0)
        .exclude(paid_in_full=1)
        .exclude(quote=1)
        .exclude(void=1)
    )

    # update aging days on all open workorders
    for x in workorders:
        if not x.date_billed:
            x.date_billed = today
        age = abs((x.date_billed - today).days)
        Workorder.objects.filter(pk=x.pk).update(aging=age)

    total_balance = workorders.aggregate(Sum("open_balance"))

    # per-customer buckets + billed-today
    for x in customers:
        if not Workorder.objects.filter(customer_id=x.id).exists():
            continue

        base_qs = workorders.filter(customer_id=x.id).exclude(billed=0).exclude(
            paid_in_full=1
        )

        current = base_qs.exclude(aging__gt=29).aggregate(Sum("open_balance"))
        current = list(current.values())[0] or Decimal("0.00")

        thirty = (
            base_qs.exclude(aging__lt=30)
            .exclude(aging__gt=59)
            .aggregate(Sum("open_balance"))
        )
        thirty = list(thirty.values())[0] or Decimal("0.00")

        sixty = (
            base_qs.exclude(aging__lt=60)
            .exclude(aging__gt=89)
            .aggregate(Sum("open_balance"))
        )
        sixty = list(sixty.values())[0] or Decimal("0.00")

        ninety = (
            base_qs.exclude(aging__lt=90)
            .exclude(aging__gt=119)
            .aggregate(Sum("open_balance"))
        )
        ninety = list(ninety.values())[0] or Decimal("0.00")

        onetwenty = (
            base_qs.exclude(aging__lt=120).aggregate(Sum("open_balance"))
        )
        onetwenty = list(onetwenty.values())[0] or Decimal("0.00")

        total = base_qs.aggregate(Sum("open_balance"))
        total = list(total.values())[0] or Decimal("0.00")

        # NEW: billed today for this customer
        billed_today_qs = base_qs.filter(date_billed__date=today_date)
        billed_today = billed_today_qs.aggregate(Sum("open_balance"))
        billed_today = list(billed_today.values())[0] or Decimal("0.00")

        try:
            Araging.objects.filter(customer_id=x.id).update(
                hr_customer=x.company_name,
                date=today,
                current=current,
                thirty=thirty,
                sixty=sixty,
                ninety=ninety,
                onetwenty=onetwenty,
                total=total,
                billed_today=billed_today,  # NEW
            )
        except Araging.DoesNotExist:
            Araging.objects.create(
                customer_id=x.id,
                hr_customer=x.company_name,
                date=today,
                current=current,
                thirty=thirty,
                sixty=sixty,
                ninety=ninety,
                onetwenty=onetwenty,
                total=total,
                billed_today=billed_today,  # NEW
            )

    # If you want a grand total of billed-today across all customers:
    ar = Araging.objects.all()
    total_billed_today = (
        ar.aggregate(Sum("billed_today"))["billed_today__sum"] or Decimal("0.00")
    )
    print("Total billed today:", total_billed_today)



# def krueger_ar_aging():
#     # update_ar = request.GET.get('up')
#     # print('update')
#     # print(update_ar)
#     # #customers = Workorder.objects.all().exclude(quote=1).exclude(paid_in_full=1).exclude(billed=0)
#     today = timezone.now()
#     customers = Customer.objects.all()
#     ar = Krueger_Araging.objects.all()
#     workorders = Workorder.objects.filter().exclude(billed=0).exclude(paid_in_full=1).exclude(quote=1).exclude(void=1).exclude(internal_company='LK Design')
#     for x in workorders:
#         #print(x.id)
#         if not x.date_billed:
#             x.date_billed = today
#         age = x.date_billed - today
#         age = abs((age).days)
#         print(age)
#         Workorder.objects.filter(pk=x.pk).update(aging = age)
#     total_balance = workorders.filter().exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
#     for x in customers:
#         # try:
#         #     #Get the Araging customer and check to see if aging has been updated today
#         #     modified = Araging.objects.get(customer=x.id)
#         #     print(x.company_name)
#         #     day = today.strftime('%Y-%m-%d')
#         #     day = str(day)
#         #     date = str(modified.date)
#         #     print(day)
#         #     print(date)
#         #     if day == date:
#         #         #Don't update, as its been done today
#         #         print('today')
#         #         update = 0
#         #         if update_ar == '1':
#         #             print('update')
#         #             update = 1
#         #     else:
#         #         update = 1
#         # except:
#         #     update = 1
#         #Update the Araging that needs to be done
#         # if update == 1:
#         if Workorder.objects.filter(customer_id = x.id).exists():
#             current = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__gt = 29).aggregate(Sum('open_balance'))
#             try:
#                 current = list(current.values())[0]
#             except:
#                 current = 0
#             thirty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 30).exclude(aging__gt = 59).aggregate(Sum('open_balance'))
#             try: 
#                 thirty = list(thirty.values())[0]
#             except:
#                 thirty = 0
#             sixty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 60).exclude(aging__gt = 89).aggregate(Sum('open_balance'))
#             try:
#                 sixty = list(sixty.values())[0]
#             except:
#                 sixty = 0
#             ninety = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 90).exclude(aging__gt = 119).aggregate(Sum('open_balance'))
#             try:
#                 ninety = list(ninety.values())[0]
#             except:
#                 ninety = 0
#             onetwenty = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).exclude(aging__lt = 120).aggregate(Sum('open_balance'))
#             try:
#                 onetwenty = list(onetwenty.values())[0]
#             except:
#                 onetwenty = 0
#             total = workorders.filter(customer_id = x.id).exclude(billed=0).exclude(paid_in_full=1).aggregate(Sum('open_balance'))
#             try:
#                 total = list(total.values())[0]
#             except:
#                 total = 0
#             try: 
#                 obj = Krueger_Araging.objects.get(customer_id=x.id)
#                 Krueger_Araging.objects.filter(customer_id=x.id).update(hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
#             except:
#                 obj = Krueger_Araging(customer_id=x.id,hr_customer=x.company_name, date=today, current=current, thirty=thirty, sixty=sixty, ninety=ninety, onetwenty=onetwenty, total=total)
#                 obj.save()
#     ar = Krueger_Araging.objects.all().order_by('hr_customer')
#     #total_current = Araging.objects.filter().aggregate(Sum('current'))
#     total_current = ar.filter().aggregate(Sum('current'))
#     # total_thirty = ar.filter().aggregate(Sum('thirty'))
#     # total_sixty = ar.filter().aggregate(Sum('sixty'))
#     # total_ninety = ar.filter().aggregate(Sum('ninety'))
#     # total_onetwenty = ar.filter().aggregate(Sum('onetwenty'))
#     print(total_current)
    
#     # #print(ar)
#     # context = {
#     #     'total_current':total_current,
#     #     'total_thirty':total_thirty,
#     #     'total_sixty':total_sixty,
#     #     'total_ninety':total_ninety,
#     #     'total_onetwenty':total_onetwenty,
#     #     'total_balance':total_balance,
#     #     'ar': ar
#     # }
#     # return render(request, 'finance/reports/ar_aging.html', context)

def krueger_ar_aging():
    today = timezone.now()
    today_date = today.date()
    zero = Decimal("0.00")

    # Base queryset for the non-LK statement dashboard
    workorders = (
        Workorder.objects
        .exclude(void=1)
        .exclude(quote=1)
        .exclude(internal_company="LK Design")
        .filter(
            Q(date_billed__isnull=False) | Q(billed=1)
        )
        .select_related("customer")
    )

    # Keep legacy aging field updated for any older pages still using it
    for wo in workorders:
        billed_date = getattr(wo, "date_billed", None)

        if billed_date:
            try:
                billed_date = billed_date.date()
            except Exception:
                pass
        else:
            billed_date = today_date

        age = max((today_date - billed_date).days, 0)
        Workorder.objects.filter(pk=wo.pk).update(aging=age)

    # Refresh queryset after aging updates
    workorders = (
        Workorder.objects
        .exclude(void=1)
        .exclude(quote=1)
        .exclude(internal_company="LK Design")
        .filter(
            Q(date_billed__isnull=False) | Q(billed=1)
        )
        .select_related("customer")
    )

    customers = Customer.objects.all()

    for customer in customers:
        customer_qs = workorders.filter(customer_id=customer.id)

        if not customer_qs.exists():
            continue

        current = (
            customer_qs.filter(Q(aging__isnull=True) | Q(aging__lte=29))
            .aggregate(total=Sum("open_balance"))["total"]
            or zero
        )

        thirty = (
            customer_qs.filter(aging__gte=30, aging__lte=59)
            .aggregate(total=Sum("open_balance"))["total"]
            or zero
        )

        sixty = (
            customer_qs.filter(aging__gte=60, aging__lte=89)
            .aggregate(total=Sum("open_balance"))["total"]
            or zero
        )

        ninety = (
            customer_qs.filter(aging__gte=90, aging__lte=119)
            .aggregate(total=Sum("open_balance"))["total"]
            or zero
        )

        onetwenty = (
            customer_qs.filter(aging__gte=120)
            .aggregate(total=Sum("open_balance"))["total"]
            or zero
        )

        total = customer_qs.aggregate(total=Sum("open_balance"))["total"] or zero

        Krueger_Araging.objects.update_or_create(
            customer_id=customer.id,
            defaults={
                "hr_customer": customer.company_name,
                "date": today,
                "current": current,
                "thirty": thirty,
                "sixty": sixty,
                "ninety": ninety,
                "onetwenty": onetwenty,
                "total": total,
            },
        )

    grand_total = (
        Krueger_Araging.objects.aggregate(total=Sum("total"))["total"] or zero
    )
    print("Krueger total:", grand_total)

ZERO = Decimal("0.00")


def _payer_band(avg_days):
    if avg_days is None:
        return ""
    if avg_days <= 15:
        return "fast"
    if avg_days <= 35:
        return "moderate"
    return "slow"


def _safe_days_between(start_date, end_date):
    if not start_date or not end_date:
        return None

    if hasattr(start_date, "date"):
        start_date = start_date.date()
    if hasattr(end_date, "date"):
        end_date = end_date.date()

    days = (end_date - start_date).days
    return days if days >= 0 else None


def build_ar_slowpayer_snapshot(as_of_date=None):
    """
    Daily snapshot builder for AR slow-payer history.

    Uses live AR logic directionally:
    - only billed, non-void, non-quote workorders
    - only closed/fully-applied workorders with value
    - measures days from billed date to paid date
    """
    as_of_date = as_of_date or timezone.localdate()

    run = ArSlowPayerSnapshotRun.objects.create(
        as_of_date=as_of_date,
        status="running",
    )

    overall_days = []
    row_count = 0
    customer_count = 0
    slow_count = 0

    try:
        workorders = (
            Workorder.objects
            .filter(billed=True)
            .exclude(void=1)
            .exclude(quote=1)
            .select_related("customer")
            .order_by("customer_id", "workorder")
        )

        customer_map = {}

        for wo in workorders:
            live = live_open_balance(wo)

            if live["total_due"] <= ZERO:
                continue

            # snapshot closed paid behavior only
            if live["open_bal"] != ZERO:
                continue

            customer_id = wo.customer_id
            if not customer_id:
                continue

            date_billed = getattr(wo, "date_billed", None)
            date_paid = _get_paid_date(wo)

            days = _safe_days_between(date_billed, date_paid)
            if days is None:
                continue

            bucket = customer_map.setdefault(
                customer_id,
                {
                    "customer": wo.customer,
                    "company_name": getattr(wo.customer, "company_name", "") or "",
                    "days": [],
                    "total_closed_revenue": ZERO,
                },
            )

            bucket["days"].append(days)
            bucket["total_closed_revenue"] += live["total_due"]

        snapshot_rows = []

        for customer_id, bucket in customer_map.items():
            days_list = bucket["days"]
            if not days_list:
                continue

            closed_count = len(days_list)
            avg_days = Decimal(str(round(sum(days_list) / closed_count, 2)))
            min_days = min(days_list)
            max_days = max(days_list)
            total_closed_revenue = bucket["total_closed_revenue"]
            payer_band = _payer_band(avg_days)

            # simple score: heavier weight on avg days, slight weight on count
            score = Decimal(str(round(float(avg_days) * (1 + min(closed_count, 25) / 100), 2)))

            snapshot_rows.append(
                ArSlowPayerSnapshot(
                    run=run,
                    customer=bucket["customer"],
                    company_name=bucket["company_name"],
                    closed_workorder_count=closed_count,
                    avg_days_to_pay=avg_days,
                    min_days_to_pay=min_days,
                    max_days_to_pay=max_days,
                    total_closed_revenue=total_closed_revenue,
                    score=score,
                    payer_band=payer_band,
                )
            )

            overall_days.extend(days_list)
            row_count += closed_count
            customer_count += 1
            if payer_band == "slow":
                slow_count += 1

        with transaction.atomic():
            ArSlowPayerSnapshot.objects.filter(run=run).delete()
            if snapshot_rows:
                ArSlowPayerSnapshot.objects.bulk_create(snapshot_rows, batch_size=500)

            overall_avg = (
                Decimal(str(round(sum(overall_days) / len(overall_days), 2)))
                if overall_days else ZERO
            )

            run.customer_count = customer_count
            run.closed_workorder_count = row_count
            run.avg_days_to_pay_overall = overall_avg
            run.slow_payer_count = slow_count
            run.status = "complete"
            run.save(
                update_fields=[
                    "customer_count",
                    "closed_workorder_count",
                    "avg_days_to_pay_overall",
                    "slow_payer_count",
                    "status",
                ]
            )

    except Exception as exc:
        run.status = "failed"
        run.notes = str(exc)
        run.save(update_fields=["status", "notes"])
        raise

    return run
