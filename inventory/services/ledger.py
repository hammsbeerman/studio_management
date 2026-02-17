from decimal import Decimal
from typing import Optional
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta, datetime

from inventory.models import InventoryMaster, InventoryLedger, Inventory
from retail.models import RetailSale, RetailSaleLine

from inventory.services.uom import qty_to_base


def record_inventory_movement(
    *,
    inventory_item: InventoryMaster,
    qty_delta,
    source_type: str,
    source_id=None,
    note: str = "",
) -> InventoryLedger:
    """
    Central helper to record a stock movement.

    - inventory_item: InventoryMaster instance
    - qty_delta: positive = stock in, negative = stock out (Decimal or castable)
    - source_type: one of InventoryLedger.SOURCE_TYPE_CHOICES
    - source_id: optional reference to originating record (invoice item id, sale id, etc.)
    - note: free-form description
    """
    return InventoryLedger.objects.create(
        inventory_item=inventory_item,
        qty_delta=Decimal(qty_delta),
        source_type=source_type,
        source_id=str(source_id) if source_id is not None else None,
        note=note or "",
    )


def get_on_hand(item: InventoryMaster) -> Decimal:
    """
    Compute on-hand quantity for an item.

    - Primary source: InventoryLedger (sum of qty_delta)
    - If no ledger entries yet, fall back to Inventory.current_stock
      so legacy data still shows something.
    """
    # 1) Sum ledger entries if any
    agg = (
        InventoryLedger.objects
        .filter(inventory_item=item)
        .aggregate(total=Sum("qty_delta"))
    )

    total = agg["total"]

    # If we have *any* ledger rows (even if the sum is 0), trust the ledger.
    if total is not None:
        return total

    # 2) Fallback: parse current_stock from Inventory rows (legacy)
    inv_qs = Inventory.objects.filter(internal_part_number=item)
    fallback = Decimal("0")

    for row in inv_qs:
        cs = getattr(row, "current_stock", "") or "0"
        try:
            fallback += Decimal(str(cs))
        except Exception:
            # ignore bad legacy values
            continue

    return fallback

def _resolve_line_qty_base(line) -> Decimal:
    return qty_to_base(line.qty or 0, getattr(line, "sold_variation", None))

def record_pos_sale_to_ledger(sale: RetailSale) -> None:
    """
    Log stock OUT for each inventory-backed line in a POS sale.
    """
    for line in sale.lines.filter(inventory__isnull=False):
        qty_base = _resolve_line_qty_base(line)
        if qty_base == 0:
            continue

        record_inventory_movement(
            inventory_item=line.inventory,
            qty_delta=-qty_base,  # stock out in base units
            source_type="POS_SALE",
            source_id=str(sale.id),
            note=f"POS sale #{sale.id}",
        )


def record_pos_refund_to_ledger(
    refund_sale: RetailSale,
    original_sale: Optional[RetailSale] = None,
) -> None:
    """
    Log stock IN for each inventory-backed line in a POS refund.
    """
    for line in refund_sale.lines.filter(inventory__isnull=False):
        qty_base = _resolve_line_qty_base(line)
        if qty_base == 0:
            continue

        record_inventory_movement(
            inventory_item=line.inventory,
            qty_delta=qty_base,  # stock returns in base units
            source_type="POS_REFUND",
            source_id=str(refund_sale.id),
            note=(
                f"POS refund #{refund_sale.id}"
                + (f" for sale #{original_sale.id}" if original_sale else "")
            ),
        )

def _normalize_range(start=None, end=None):
    """
    Normalize a date/time range for ledger queries.

    If both start and end are None, default to the last 30 days.
    Accepts either date or datetime objects; returns timezone-aware datetimes.
    """
    tz = timezone.get_current_timezone()
    now = timezone.now()

    if start is None and end is None:
        end_dt = now
        start_dt = end_dt - timedelta(days=30)
    else:
        start_dt = start or (now - timedelta(days=30))
        end_dt = end or now

    # If we got dates, make them datetimes
    from datetime import date, datetime as _dt

    if isinstance(start_dt, date) and not isinstance(start_dt, _dt):
        start_dt = _dt.combine(start_dt, _dt.min.time())
    if isinstance(end_dt, date) and not isinstance(end_dt, _dt):
        end_dt = _dt.combine(end_dt, _dt.max.time())

    # Ensure they're timezone-aware
    if timezone.is_naive(start_dt):
        start_dt = tz.localize(start_dt)
    if timezone.is_naive(end_dt):
        end_dt = tz.localize(end_dt)

    return start_dt, end_dt


def get_qty_sold_for_item(
    item: InventoryMaster,
    *,
    start=None,
    end=None,
) -> Decimal:
    """
    Return net POS quantity sold for a single item in a date range.

    Uses InventoryLedger rows where source_type is POS_SALE / POS_REFUND.

    Convention:
    - POS_SALE rows are negative (stock out)
    - POS_REFUND rows are positive (stock back in)

    qty_sold = max(0, -SUM(qty_delta))
    """
    start_dt, end_dt = _normalize_range(start, end)

    agg = (
        InventoryLedger.objects
        .filter(
            inventory_item=item,
            source_type__in=["POS_SALE", "POS_REFUND"],
            when__gte=start_dt,
            when__lte=end_dt,
        )
        .aggregate(total=Sum("qty_delta"))
    )
    total = agg["total"] or Decimal("0")
    net_sold = -total
    if net_sold < 0:
        net_sold = Decimal("0")
    return net_sold


def get_qty_sold_summary(*, start=None, end=None):
    """
    Summarize POS quantity sold per item over a date range.

    Returns a list of dicts:
        {
            "item": InventoryMaster,
            "qty_sold": Decimal,
        }

    Only items with qty_sold > 0 are included.
    """
    start_dt, end_dt = _normalize_range(start, end)

    qs = (
        InventoryLedger.objects
        .filter(
            source_type__in=["POS_SALE", "POS_REFUND"],
            when__gte=start_dt,
            when__lte=end_dt,
        )
        .values("inventory_item")
        .annotate(total=Sum("qty_delta"))
    )

    rows = []
    for row in qs:
        item_id = row["inventory_item"]
        total = row["total"] or Decimal("0")
        net_sold = -total
        if net_sold <= 0:
            continue

        try:
            item = InventoryMaster.objects.get(pk=item_id)
        except InventoryMaster.DoesNotExist:
            continue

        rows.append(
            {
                "item": item,
                "qty_sold": net_sold,
            }
        )

    # sort by qty_sold desc
    rows.sort(key=lambda r: r["qty_sold"], reverse=True)
    return rows


def get_stock_valuation_for_item(item: InventoryMaster) -> Decimal:
    """
    Simple inventory valuation for a single item.

    valuation = get_on_hand(item) * item.unit_cost
    """
    on_hand = get_on_hand(item)
    cost = item.unit_cost or Decimal("0")
    return (on_hand * cost).quantize(Decimal("0.0001"))


def get_negative_stock_items(threshold: Decimal = Decimal("0")):
    """
    Return a list of (item, on_hand) where on_hand <= threshold.

    This is useful for admin reports or POS warnings.
    """
    out = []
    for item in InventoryMaster.objects.all():
        on_hand = get_on_hand(item)
        if on_hand <= threshold:
            out.append((item, on_hand))
    return out

def get_qty_sold_for_item(
    item: InventoryMaster,
    *,
    start_date,
    end_date,
) -> Decimal:
    """
    Net POS quantity sold for a single item in a date range.

    Net sold = -SUM(qty_delta) for ledger rows:
      - source_type in (POS_SALE, POS_REFUND)
      - within [start_date, end_date] (inclusive)
    """
    start_dt = datetime.combine(start_date, datetime.min.time()).replace(microsecond=0)
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0)

    agg = (
        InventoryLedger.objects
        .filter(
            inventory_item=item,
            source_type__in=["POS_SALE", "POS_REFUND"],
            when__gte=start_dt,
            when__lte=end_dt,
        )
        .aggregate(total=Sum("qty_delta"))
    )

    total = agg["total"] or Decimal("0")
    net_sold = -total
    if net_sold < 0:
        net_sold = Decimal("0")
    return net_sold


def get_qty_sold_summary(*, start_date, end_date):
    """
    POS Qty-sold summary, one row per InventoryMaster.

    Returns a list of dicts:
      {
        "item": InventoryMaster,
        "qty_sold": Decimal,
        "on_hand": Decimal,
      }
    """
    start_dt = datetime.combine(start_date, datetime.min.time()).replace(microsecond=0)
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0)

    qs = (
        InventoryLedger.objects
        .filter(
            source_type__in=["POS_SALE", "POS_REFUND"],
            when__gte=start_dt,
            when__lte=end_dt,
        )
        .values("inventory_item")
        .annotate(qty_delta_sum=Sum("qty_delta"))
    )

    rows = []
    for row in qs:
        item_id = row["inventory_item"]
        qty_delta_sum = row["qty_delta_sum"] or 0
        net_sold = -qty_delta_sum
        if net_sold == 0:
            continue

        try:
            item = InventoryMaster.objects.get(pk=item_id)
        except InventoryMaster.DoesNotExist:
            continue

        rows.append(
            {
                "item": item,
                "qty_sold": net_sold,
                "on_hand": get_on_hand(item),
            }
        )

    rows.sort(key=lambda r: r["qty_sold"], reverse=True)
    return rows


def get_stock_valuation_for_item(item: InventoryMaster) -> Decimal:
    """
    Simple inventory valuation for a single item.

    valuation = on_hand * unit_cost
    """
    on_hand = get_on_hand(item)
    cost = item.unit_cost or Decimal("0")
    return (on_hand * cost).quantize(Decimal("0.0001"))


def get_stock_alerts(
    *,
    negative_threshold: Decimal = Decimal("0"),
    low_threshold: Optional[Decimal] = None,
):
    """
    Return (negative_items, low_items):

      negative_items: list[(item, on_hand)] where on_hand <= negative_threshold
      low_items:      list[(item, on_hand)] where
                      negative_threshold < on_hand <= low_threshold

    Only non-inventory items (non_inventory=False) are considered.
    """
    negative = []
    low = []

    qs = InventoryMaster.objects.filter(non_inventory=False)

    for item in qs:
        on_hand = get_on_hand(item)

        if on_hand <= negative_threshold:
            negative.append((item, on_hand))
        elif low_threshold is not None and on_hand <= low_threshold:
            low.append((item, on_hand))

    return negative, low