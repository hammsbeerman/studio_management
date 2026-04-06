from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from customers.models import Contact
from finance.helpers_ar import live_open_balance
from workorders.models import Workorder


ZERO = Decimal("0.00")
VALID_COMPANIES = ["Krueger Printing", "LK Design", "Office Supplies"]


def normalize_open_balance(value):
    """
    Normalize live_open_balance output to a Decimal.

    Supported inputs:
    - Decimal
    - int / float
    - dict with:
        - open_bal
        - open_balance
        - open_balance__sum
    """
    if value is None:
        return ZERO

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    if isinstance(value, dict):
        if value.get("open_bal") is not None:
            return normalize_open_balance(value["open_bal"])
        if value.get("open_balance") is not None:
            return normalize_open_balance(value["open_balance"])
        if value.get("open_balance__sum") is not None:
            return normalize_open_balance(value["open_balance__sum"])
        return ZERO

    try:
        return Decimal(str(value))
    except Exception:
        return ZERO


def normalize_to_date(value):
    """
    Normalize date/datetime values to a plain date.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return value.date()
    except Exception:
        return None


def get_live_statement_queryset(companies=None, customer=None):
    """
    Shared base queryset for live AR-backed statements.

    Rules:
    - exclude void workorders
    - exclude quotes using the actual char-based quote field
    - require completed workorders
    - require billed work: billed=True or date_billed present
    - default statement behavior excludes LK Design unless companies are passed
    """
    qs = (
        Workorder.objects
        .filter(void=False)
        .filter(completed=True)
        .filter(
            Q(quote="0") | Q(quote=0) | Q(quote=False) | Q(quote__isnull=True)
        )
        .filter(
            Q(date_billed__isnull=False) | Q(billed=True)
        )
        .select_related("customer")
    )

    if customer is not None:
        qs = qs.filter(customer=customer)

    if companies:
        qs = qs.filter(internal_company__in=companies)
    else:
        qs = qs.exclude(internal_company="LK Design")

    return qs

def workorder_aging_days(workorder, today=None):
    today = normalize_to_date(today) or date.today()
    billed_date = normalize_to_date(getattr(workorder, "date_billed", None))

    if not billed_date:
        return 0

    return max((today - billed_date).days, 0)


def bucket_for_days(days):
    if days < 30:
        return "current"
    if days < 60:
        return "thirty"
    if days < 90:
        return "sixty"
    if days < 120:
        return "ninety"
    return "onetwenty"


def get_header_variant(companies_present):
    selection = set(companies_present or [])

    lk = "LK Design" in selection
    kr = "Krueger Printing" in selection
    office = "Office Supplies" in selection

    if lk and not (kr or office):
        return 3
    if lk and (kr or office):
        return 2
    return 1


def build_live_statement_rows(companies=None, customer=None):
    qs = get_live_statement_queryset(companies=companies, customer=customer)
    today = timezone.now().date()

    rows = []

    for workorder in qs.order_by("date_billed", "workorder"):
        if not workorder.customer_id:
            continue

        try:
            open_balance = normalize_open_balance(live_open_balance(workorder))
        except Exception:
            continue

        if open_balance <= ZERO:
            continue

        days = workorder_aging_days(workorder, today=today)
        bucket = bucket_for_days(days)

        workorder.open_balance = open_balance
        workorder.statement_open_balance = open_balance
        workorder.statement_aging_days = days

        rows.append({
            "workorder": workorder,
            "customer": workorder.customer,
            "open_balance": open_balance,
            "days": days,
            "bucket": bucket,
        })

    return rows


def group_statement_rows(rows):
    grouped = defaultdict(list)

    for row in rows:
        customer = row.get("customer")
        if customer:
            grouped[customer].append(row)

    return grouped


def build_statement_summary_rows(companies=None):
    rows = build_live_statement_rows(companies=companies)
    summary = {}

    for row in rows:
        customer = row["customer"]
        if not customer:
            continue

        customer_id = customer.id

        if customer_id not in summary:
            summary[customer_id] = {
                "customer": customer,
                "hr_customer": customer.company_name if customer else "",
                "current": ZERO,
                "thirty": ZERO,
                "sixty": ZERO,
                "ninety": ZERO,
                "onetwenty": ZERO,
                "total": ZERO,
            }

        bucket = row["bucket"]
        open_balance = row["open_balance"]

        summary[customer_id][bucket] += open_balance
        summary[customer_id]["total"] += open_balance

    return sorted(
        summary.values(),
        key=lambda r: (r["hr_customer"] or "").lower()
    )


def build_customer_statement_data(qs):
    customer_map = {}
    today = timezone.now().date()

    for workorder in qs:
        if not workorder.customer_id:
            continue

        try:
            open_balance = normalize_open_balance(live_open_balance(workorder))
        except Exception:
            continue

        if open_balance <= ZERO:
            continue

        days = workorder_aging_days(workorder, today=today)

        workorder.open_balance = open_balance
        workorder.statement_open_balance = open_balance
        workorder.statement_aging_days = days

        customer_id = workorder.customer_id

        if customer_id not in customer_map:
            customer_map[customer_id] = {
                "customer": workorder.customer,
                "workorders": [],
                "total_open_balance": {"open_balance__sum": ZERO},
                "contact": "",
                "companies_present": set(),
            }

            try:
                customer_map[customer_id]["contact"] = Contact.objects.get(
                    id=workorder.customer.contact.id
                )
            except Exception:
                customer_map[customer_id]["contact"] = ""

        customer_map[customer_id]["workorders"].append(workorder)
        customer_map[customer_id]["total_open_balance"]["open_balance__sum"] += open_balance

        if getattr(workorder, "internal_company", None):
            customer_map[customer_id]["companies_present"].add(workorder.internal_company)

    customer_data = []

    for _, data in sorted(
        customer_map.items(),
        key=lambda item: (
            (item[1]["customer"].company_name or "").lower()
            if item[1]["customer"] else ""
        )
    ):
        workorders = sorted(
            data["workorders"],
            key=lambda w: (
                normalize_to_date(getattr(w, "date_billed", None)) or today,
                w.workorder or 0,
            )
        )

        companies_present = sorted(data["companies_present"])
        header_variant = get_header_variant(companies_present)

        customer_data.append({
            "customer": data["customer"],
            "workorders": workorders,
            "total_open_balance": data["total_open_balance"],
            "contact": data["contact"],
            "companies_present": companies_present,
            "header_variant": header_variant,
        })

    return customer_data


def sum_statement_summary_field(statement_rows, field):
    return sum((row.get(field, ZERO) for row in statement_rows), ZERO)