from datetime import date as date_cls
from django.utils import timezone

from retail.models import Delivery


def sync_delivery_for_workorder(workorder):
    """
    Ensure the Delivery table matches the workorder's delivery flags.

    Rules:
    - If the WO indicates it needs delivery (requires_delivery or delivery_pickup == 'Delivery'),
      ensure there is ONE open Delivery row (delivered_at is null).
    - If it no longer needs delivery, delete any open Delivery rows for it.
    """

    # Decide if this WO should appear on the delivery report
    needs_delivery = (
        getattr(workorder, "requires_delivery", False)
        or getattr(workorder, "delivery_pickup", None) == "Delivery"
    )

    # Base queryset for this WO's *open* deliveries
    open_qs = Delivery.objects.filter(
        workorder=workorder,
        delivered_at__isnull=True,
    )

    if not needs_delivery:
        # No longer needs delivery → remove open deliveries
        if open_qs.exists():
            open_qs.delete()
        return

    # It DOES need delivery
    if open_qs.exists():
        # Already have an open Delivery row → optionally update date/notes
        delivery = open_qs.first()

        # Keep scheduled_date in sync if WO has a delivery_date
        if getattr(workorder, "delivery_date", None) and delivery.scheduled_date != workorder.delivery_date:
            delivery.scheduled_date = workorder.delivery_date
            delivery.save(update_fields=["scheduled_date"])
        return

    # No open Delivery yet → create one
    # Choose a scheduled date:
    if getattr(workorder, "delivery_date", None):
        scheduled = workorder.delivery_date
    elif getattr(workorder, "date_completed", None):
        scheduled = workorder.date_completed.date()
    else:
        scheduled = timezone.localdate()

    Delivery.objects.create(
        customer=workorder.customer,
        workorder=workorder,
        sale=None,  # link a sale later if you want
        scheduled_date=scheduled,
        notes=workorder.notes or "",
        # status or sort_order if your model has defaults
    )