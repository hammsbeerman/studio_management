from decimal import Decimal
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

from django.db.models import Sum, Q  # 🔹 add Q
from django.utils import timezone

from workorders.models import WorkorderItem
from inventory.models import RetailWorkorderItem


Totals = namedtuple(
    "Totals",
    ["subtotal", "tax", "total", "wi_subtotal", "wi_tax", "pos_subtotal", "pos_tax"],
)


def compute_workorder_totals(workorder):
    """
    Single source of truth for workorder totals.

    - WorkorderItem:
        * include billable, non-parent rows
        * subtotal = sum(absolute_price)
        * tax = sum(tax_amount)

    - RetailWorkorderItem (POS):
        * subtotal = sum(total_price)
        * tax:
            - 0 if workorder or customer is tax_exempt
            - 0 if any linked RetailSale is tax_exempt or has tax_rate = 0
            - otherwise sale.tax_rate (first non-null), or 5.5% fallback

    Returns a Totals namedtuple with:
        subtotal, tax, total, wi_subtotal, wi_tax, pos_subtotal, pos_tax
    """

    # === NON-POS WORKORDER ITEMS ===
    wi_agg = (
        WorkorderItem.objects
        .filter(workorder=workorder, billable=True)
        .exclude(parent=True)
        .aggregate(
            sum_abs=Sum("absolute_price"),
            sum_tax=Sum("tax_amount"),
        )
    )

    wi_subtotal = wi_agg["sum_abs"] or Decimal("0")
    wi_tax = wi_agg["sum_tax"] or Decimal("0")

    # === POS ITEMS ===
    pos_qs = RetailWorkorderItem.objects.filter(workorder=workorder)
    pos_agg = pos_qs.aggregate(sum_total=Sum("total_price"))
    pos_subtotal = pos_agg["sum_total"] or Decimal("0")

    # tax-exempt if either the workorder OR the customer is tax_exempt
    tax_exempt = False
    if getattr(workorder, "tax_exempt", False):
        tax_exempt = True

    customer = getattr(workorder, "customer", None)
    if customer is not None and getattr(customer, "tax_exempt", False):
        tax_exempt = True

    pos_tax = Decimal("0")

    if pos_subtotal and not tax_exempt:
        # 🔹 sale-level override: if ANY linked sale is tax-exempt or has tax_rate=0,
        # treat POS as non-taxable (this is your "Don't charge tax on this sale" toggle).
        any_sale_exempt = pos_qs.filter(
            Q(sale__tax_exempt=True) | Q(sale__tax_rate=Decimal("0.000"))
        ).exists()

        if not any_sale_exempt:
            # Try to use the sale's tax_rate if present, else fall back to WI 5.5%
            sale_tax_rate = (
                pos_qs.values_list("sale__tax_rate", flat=True)
                .exclude(sale__tax_rate__isnull=True)
                .first()
            )

            if not sale_tax_rate or sale_tax_rate == 0:
                sale_tax_rate = Decimal("0.055")

            pos_tax = (pos_subtotal * sale_tax_rate).quantize(Decimal("0.01"))

    subtotal = wi_subtotal + pos_subtotal
    tax = wi_tax + pos_tax
    total = subtotal + tax

    logger.info(
        "WO %s totals: subtotal=%s, tax=%s, total=%s (wi: %s/%s, pos: %s/%s)",
        workorder.workorder,
        subtotal, tax, total,
        wi_subtotal, wi_tax,
        pos_subtotal, pos_tax,
    )

    return Totals(
        subtotal=subtotal,
        tax=tax,
        total=total,
        wi_subtotal=wi_subtotal,
        wi_tax=wi_tax,
        pos_subtotal=pos_subtotal,
        pos_tax=pos_tax,
    )

def recalc_workorder_balances(workorder):
    """
    Recompute totals + open balance + paid_in_full based on:
      - compute_workorder_totals(workorder).total
      - workorder.amount_paid
    """
    totals = compute_workorder_totals(workorder)

    amount_paid = workorder.amount_paid or Decimal("0.00")
    total_balance = totals.total.quantize(Decimal("0.01"))
    open_balance = (total_balance - amount_paid).quantize(Decimal("0.01"))

    # clamp tiny rounding noise
    if abs(open_balance) < Decimal("0.01"):
        open_balance = Decimal("0.00")

    workorder.total_balance = total_balance
    workorder.open_balance = open_balance
    workorder.paid_in_full = (open_balance <= Decimal("0.00"))

    # optional: if it’s fully paid, set date_paid
    if workorder.paid_in_full and not workorder.date_paid:
        workorder.date_paid = timezone.now().date()

    # don’t auto-clear date_paid unless you want that behavior
    # if not workorder.paid_in_full:
    #     workorder.date_paid = None

    workorder.save(update_fields=["total_balance", "open_balance", "paid_in_full", "date_paid"])
    return totals