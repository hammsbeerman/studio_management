from __future__ import annotations
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Max

from retail.models import RetailSale, Delivery, DeliveryRouteEntry
from workorders.models import Workorder
from customers.models import Customer

# If you have choices/constants on the model, use those instead:
STATUS_PENDING = getattr(Delivery, "STATUS_PENDING", "PENDING")
STATUS_CANCELLED = getattr(Delivery, "STATUS_CANCELLED", "CANCELLED")


def get_sticky_delivery_date(request):
    """
    Read last used delivery date from session or default to today.
    """
    last_date_str = request.session.get("last_delivery_date")
    if last_date_str:
        try:
            return datetime.strptime(last_date_str, "%Y-%m-%d").date()
        except Exception:
            pass
    return timezone.localdate()


def set_sticky_delivery_date(request, date_obj):
    """
    Save last used delivery date in session.
    """
    request.session["last_delivery_date"] = date_obj.strftime("%Y-%m-%d")


def ensure_sale_delivery(sale: RetailSale, scheduled_date: date) -> Delivery:
    """
    Ensure there is a Delivery row for this sale on the given date.

    - If none exists, create a new PENDING delivery.
    - If one exists (even if CANCELLED), update the date/customer and
      flip it back to PENDING so it shows on the delivery report.
    """
    if sale is None:
        raise ValueError("sale is required")

    delivery, created = Delivery.objects.get_or_create(
        sale=sale,
        defaults={
            "customer": sale.customer,
            "scheduled_date": scheduled_date,
            "status": STATUS_PENDING,
        },
    )

    changed = False

    # keep delivery aligned with sale + chosen date
    if delivery.customer != sale.customer:
        delivery.customer = sale.customer
        changed = True

    if delivery.scheduled_date != scheduled_date:
        delivery.scheduled_date = scheduled_date
        changed = True

    # 🔑 revive cancelled deliveries when workorder turns it back on
    if delivery.status == STATUS_CANCELLED:
        delivery.status = STATUS_PENDING
        changed = True

    if changed:
        delivery.save()

    # make sure the customer has a route entry (your existing function)
    if delivery.customer:
        ensure_route_entry_for_customer(delivery.customer)

    return delivery


def sync_workorder_delivery_from_sale(sale: RetailSale, scheduled_date=None):
    """
    Keep Workorder delivery flags in sync with sale.requires_delivery.

    If scheduled_date is provided and sale.requires_delivery is True,
    update Workorder.delivery_date as well.
    """
    wo = getattr(sale, "workorder", None)
    if not wo:
        return

    wo.requires_delivery = sale.requires_delivery
    if sale.requires_delivery and scheduled_date is not None:
        wo.delivery_date = scheduled_date
    elif not sale.requires_delivery:
        wo.delivery_date = None

    wo.save()

def ensure_route_entry_for_customer(customer: Customer) -> DeliveryRouteEntry:
    entry, created = DeliveryRouteEntry.objects.get_or_create(customer=customer)
    if created:
        max_order = DeliveryRouteEntry.objects.aggregate(m=Max("sort_order"))["m"] or 0
        entry.sort_order = max_order + 10
        entry.save()
    return entry

def ensure_workorder_delivery(wo, scheduled_date: date) -> Delivery:
    """
    Ensure a Delivery row exists for a workorder that does NOT necessarily
    have a POS sale.

    - Creates a new Delivery if needed.
    - Keeps customer/date in sync.
    - Revives CANCELLED to PENDING when turning back on.
    """
    delivery, created = Delivery.objects.get_or_create(
        workorder=wo,
        defaults={
            "customer": wo.customer,
            "scheduled_date": scheduled_date,
            "status": STATUS_PENDING,
        },
    )

    changed = False

    if delivery.customer != wo.customer:
        delivery.customer = wo.customer
        changed = True

    if delivery.scheduled_date != scheduled_date:
        delivery.scheduled_date = scheduled_date
        changed = True

    if delivery.status == STATUS_CANCELLED:
        delivery.status = STATUS_PENDING
        changed = True

    if changed:
        delivery.save()

    if delivery.customer:
        ensure_route_entry_for_customer(delivery.customer)

    return delivery


def cancel_sale_delivery(sale) -> None:
    Delivery.objects.filter(sale=sale).update(status=STATUS_CANCELLED)


def cancel_workorder_delivery(wo) -> None:
    Delivery.objects.filter(workorder=wo).update(status=STATUS_CANCELLED)