from decimal import Decimal
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.utils import timezone
from workorders.models import Workorder
from customers.models import Customer

AR_QUOTE_FILTER = Q(quote="0") | Q(quote=0) | Q(quote=False) | Q(quote__isnull=True)

def ar_open_workorders_qs(customer_id):
    return (
        Workorder.objects
        .filter(customer_id=customer_id)
        .filter(billed=True)
        .filter(paid_in_full=False)
        .filter(void=False)
        .filter(AR_QUOTE_FILTER)
        .order_by("workorder")
    )

def recompute_customer_open_balance(customer_id):
    open_balance = (
        Workorder.objects
        .filter(customer_id=customer_id)
        .filter(billed=True)
        .filter(paid_in_full=False)
        .filter(void=False)
        .filter(AR_QUOTE_FILTER)
        .aggregate(sum=Sum("open_balance"))
    )["sum"] or Decimal("0.00")

    Customer.objects.filter(pk=customer_id).update(open_balance=open_balance)
    return open_balance

def apply_amount_to_workorder(wo, amt, applied_date=None):
    applied_date = applied_date or timezone.now().date()

    wo_open = wo.open_balance or Decimal("0.00")
    wo_paid = wo.amount_paid or Decimal("0.00")

    new_open = wo_open - amt
    new_paid = wo_paid + amt

    paid_full = new_open <= Decimal("0.00")
    if paid_full:
        new_open = Decimal("0.00")

    Workorder.objects.filter(pk=wo.pk).update(
        open_balance=new_open,
        amount_paid=new_paid,
        paid_in_full=paid_full,
        date_paid=applied_date if paid_full else None,
    )

def reverse_amount_from_workorder(wo, amt):
    wo_open = wo.open_balance or Decimal("0.00")
    wo_paid = wo.amount_paid or Decimal("0.00")

    new_open = wo_open + amt
    new_paid = wo_paid - amt
    if new_paid < 0:
        new_paid = Decimal("0.00")

    Workorder.objects.filter(pk=wo.pk).update(
        open_balance=new_open,
        amount_paid=new_paid,
        paid_in_full=False,
        date_paid=None,
    )

def hx_ar_changed_204():
    resp = HttpResponse(status=204)
    resp["HX-Trigger"] = "arChanged"
    return resp