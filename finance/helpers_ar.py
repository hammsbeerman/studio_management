from decimal import Decimal

from django.db.models import Q, Sum, Prefetch
from django.http import HttpResponse
from django.utils import timezone

from customers.models import Customer
from finance.models import (
    GiftCertificateRedemption,
    Payments,
    WorkorderCreditMemo,
    WorkorderPayment,
)
from workorders.models import Workorder
from workorders.services.totals import compute_workorder_totals


MONEY = Decimal("0.01")
ZERO = Decimal("0.00")

AR_QUOTE_FILTER = (
    Q(quote="0")
    | Q(quote=0)
    | Q(quote=False)
    | Q(quote__isnull=True)
)


def money(value) -> Decimal:
    return Decimal(value or ZERO).quantize(MONEY)


def q_non_quote():
    return AR_QUOTE_FILTER


def workorders_base_ar_qs():
    return (
        Workorder.objects
        .filter(void=False)
        .filter(AR_QUOTE_FILTER)
        .filter(
            Q(billed=True) |
            Q(date_billed__isnull=False)
        )
        .select_related("customer")
        .prefetch_related(
            "workorderpayment_set",
            "workordercreditmemo_set",
            "giftcertificateredemption_set",
        )
    )


def customer_ar_workorders_qs(customer):
    return (
        Workorder.objects
        .filter(customer=customer, billed=True, void=False)
        .filter(AR_QUOTE_FILTER)
        .order_by("workorder")
    )


def live_applied_totals(workorder):
    payments = getattr(workorder, "workorderpayment_set", None)
    credit_memos = getattr(workorder, "workordercreditmemo_set", None)
    gift_redemptions = getattr(workorder, "giftcertificateredemption_set", None)

    if payments is not None:
        paid_amt = sum((p.payment_amount for p in payments if not p.void), ZERO)
    else:
        paid_amt = (
            WorkorderPayment.objects
            .filter(workorder=workorder, void=False)
            .aggregate(total=Sum("payment_amount"))["total"]
            or ZERO
        )

    if credit_memos is not None:
        cm_amt = sum((c.amount for c in credit_memos if not c.void), ZERO)
    else:
        cm_amt = (
            WorkorderCreditMemo.objects
            .filter(workorder=workorder, void=False)
            .aggregate(total=Sum("amount"))["total"]
            or ZERO
        )

    if gift_redemptions is not None:
        gc_amt = sum((g.amount for g in gift_redemptions if not g.void), ZERO)
    else:
        gc_amt = (
            GiftCertificateRedemption.objects
            .filter(workorder=workorder, void=False)
            .aggregate(total=Sum("amount"))["total"]
            or ZERO
        )

    return money(paid_amt), money(cm_amt), money(gc_amt)


def live_total_due(workorder):
    totals = compute_workorder_totals(workorder)
    total_due = money(getattr(totals, "total", None))

    if total_due == ZERO:
        try:
            total_due = money(workorder.open_balance)
        except Exception:
            total_due = ZERO

    return total_due


def live_open_balance(workorder):
    total_due = live_total_due(workorder)
    paid_amt, cm_amt, gc_amt = live_applied_totals(workorder)

    total_applied = money(paid_amt + cm_amt + gc_amt)
    open_bal = money(total_due - total_applied)

    if abs(open_bal) < MONEY:
        open_bal = ZERO
    if open_bal < ZERO:
        open_bal = ZERO

    return {
        "total_due": total_due,
        "paid_amt": paid_amt,
        "cm_amt": cm_amt,
        "gc_amt": gc_amt,
        "total_applied": total_applied,
        "open_bal": open_bal,
    }


def workorder_billed_date(workorder):
    if not workorder.date_billed:
        return None
    return workorder.date_billed.date() if hasattr(workorder.date_billed, "date") else workorder.date_billed


def workorder_aging_days(workorder, today_date=None):
    today_date = today_date or timezone.localdate()
    billed_date = workorder_billed_date(workorder)

    if not billed_date:
        return 0

    return max((today_date - billed_date).days, 0)


def build_live_ar_rows(workorders_qs):
    """
    Build row-level live AR workorders for report pages.
    Attaches in-memory values so legacy templates can keep using:
      x.open_balance
      x.aging
    """
    today_date = timezone.localdate()
    rows = []
    total_open = ZERO

    for workorder in workorders_qs:
        live = live_open_balance(workorder)
        open_bal = live["open_bal"]

        if open_bal <= ZERO:
            continue

        workorder.total_balance = live["total_due"]
        workorder.amount_paid = live["total_applied"]
        workorder.open_balance = open_bal
        workorder.aging = workorder_aging_days(workorder, today_date=today_date)

        rows.append(workorder)
        total_open += open_bal

    return rows, {"open_balance__sum": money(total_open)}


def build_live_aging_rows(workorders_qs, include_billed_today=False):
    """
    Build customer aging rows from live workorder math instead of snapshot tables.
    Returns rows + totals shaped to match existing templates.
    """
    today_date = timezone.localdate()
    customers = {}

    for workorder in workorders_qs:
        live = live_open_balance(workorder)
        open_bal = live["open_bal"]

        if open_bal <= ZERO:
            continue

        customer_id = workorder.customer_id
        if not customer_id:
            continue

        customer_name = (
            getattr(workorder.customer, "company_name", None)
            or workorder.hr_customer
            or f"Customer {customer_id}"
        )

        row = customers.setdefault(
            customer_id,
            {
                "customer_id": customer_id,
                "hr_customer": customer_name,
                "current": ZERO,
                "thirty": ZERO,
                "sixty": ZERO,
                "ninety": ZERO,
                "onetwenty": ZERO,
                "total": ZERO,
                "billed_today": ZERO,
            },
        )

        aging = workorder_aging_days(workorder, today_date=today_date)

        if aging < 30:
            row["current"] += open_bal
        elif aging < 60:
            row["thirty"] += open_bal
        elif aging < 90:
            row["sixty"] += open_bal
        elif aging < 120:
            row["ninety"] += open_bal
        else:
            row["onetwenty"] += open_bal

        billed_date = workorder_billed_date(workorder)
        if include_billed_today and billed_date == today_date:
            row["billed_today"] += open_bal

        row["total"] += open_bal

    ar = sorted(customers.values(), key=lambda x: (x["hr_customer"] or "").lower())

    total_current_val = sum((x["current"] for x in ar), ZERO)
    total_thirty_val = sum((x["thirty"] for x in ar), ZERO)
    total_sixty_val = sum((x["sixty"] for x in ar), ZERO)
    total_ninety_val = sum((x["ninety"] for x in ar), ZERO)
    total_onetwenty_val = sum((x["onetwenty"] for x in ar), ZERO)
    total_balance_val = sum((x["total"] for x in ar), ZERO)
    total_billed_today_val = sum((x["billed_today"] for x in ar), ZERO)

    totals = {
        "total_current": {"current__sum": money(total_current_val)},
        "total_thirty": {"thirty__sum": money(total_thirty_val)},
        "total_sixty": {"sixty__sum": money(total_sixty_val)},
        "total_ninety": {"ninety__sum": money(total_ninety_val)},
        "total_onetwenty": {"onetwenty__sum": money(total_onetwenty_val)},
        "total_balance": {"open_balance__sum": money(total_balance_val)},
        "total_billed_today": money(total_billed_today_val),
    }

    return ar, totals


def ar_open_workorders_qs(customer_id):
    workorders = (
        Workorder.objects
        .filter(customer_id=customer_id, billed=True, void=False)
        .filter(AR_QUOTE_FILTER)
        .order_by("workorder")
    )

    open_ids = []

    for workorder in workorders:
        if live_open_balance(workorder)["open_bal"] > ZERO:
            open_ids.append(workorder.pk)

    return Workorder.objects.filter(pk__in=open_ids).order_by("workorder")


def recompute_customer_open_balance(customer_id):
    workorders = (
        Workorder.objects
        .filter(customer_id=customer_id, billed=True, void=False)
        .filter(AR_QUOTE_FILTER)
        .order_by("workorder")
    )

    total_open = ZERO

    for workorder in workorders:
        total_open += live_open_balance(workorder)["open_bal"]

    total_open = money(total_open)
    Customer.objects.filter(pk=customer_id).update(open_balance=total_open)
    return total_open


def recompute_customer_credit(customer_id):
    credit = (
        Payments.objects
        .filter(customer_id=customer_id, void=False)
        .aggregate(sum=Sum("available"))["sum"]
        or ZERO
    )

    credit = money(credit)
    if credit < ZERO:
        credit = ZERO

    Customer.objects.filter(pk=customer_id).update(credit=credit)
    return credit


def get_customer_ar_summary(customer):
    workorders = customer_ar_workorders_qs(customer)

    total_due = ZERO
    total_paid = ZERO
    total_open = ZERO
    days_to_pay_list = []

    for workorder in workorders:
        data = live_open_balance(workorder)

        total_due += data["total_due"]
        total_paid += data["paid_amt"] + data["cm_amt"] + data["gc_amt"]
        total_open += data["open_bal"]

        date_paid_calc = getattr(workorder, "date_paid_calc", None)
        if data["open_bal"] == ZERO and workorder.date_billed and date_paid_calc:
            days = (date_paid_calc - workorder.date_billed).days
            if days >= 0:
                days_to_pay_list.append(days)

    avg_days = (
        sum(days_to_pay_list) / len(days_to_pay_list)
        if days_to_pay_list
        else None
    )

    return {
        "total_due": money(total_due),
        "total_paid": money(total_paid),
        "total_open": money(total_open),
        "avg_days_to_pay": avg_days,
        "days_to_pay_count": len(days_to_pay_list),
    }


def hx_ar_changed_204():
    response = HttpResponse(status=204)
    response["HX-Trigger"] = "arChanged"
    return response

def get_customer_ar_aging(customer):
    workorders = customer_ar_workorders_qs(customer)
    today_date = timezone.localdate()

    buckets = {
        "current": ZERO,
        "thirty": ZERO,
        "sixty": ZERO,
        "ninety": ZERO,
        "onetwenty": ZERO,
    }

    for workorder in workorders:
        data = live_open_balance(workorder)
        open_bal = data["open_bal"]

        if open_bal <= ZERO:
            continue

        aging = workorder_aging_days(workorder, today_date=today_date)

        if aging < 30:
            buckets["current"] += open_bal
        elif aging < 60:
            buckets["thirty"] += open_bal
        elif aging < 90:
            buckets["sixty"] += open_bal
        elif aging < 120:
            buckets["ninety"] += open_bal
        else:
            buckets["onetwenty"] += open_bal

    return {
        "current": money(buckets["current"]),
        "thirty": money(buckets["thirty"]),
        "sixty": money(buckets["sixty"]),
        "ninety": money(buckets["ninety"]),
        "onetwenty": money(buckets["onetwenty"]),
    }

