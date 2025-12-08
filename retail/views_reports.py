from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Sum, F
from django.utils.dateparse import parse_date

from .models import RetailSaleLine, RetailCashSale

@login_required
def inventory_sales_report(request):
    start = request.GET.get("start")
    end = request.GET.get("end")

    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    lines = RetailSaleLine.objects.select_related("inventory", "sale")

    if start_date:
        lines = lines.filter(sale__created_at__date__gte=start_date)
    if end_date:
        lines = lines.filter(sale__created_at__date__lte=end_date)

    # Ignore refunds in this report; or handle them separately if you prefer
    lines = lines.filter(sale__is_refund=False, inventory__isnull=False)

    summary = (
        lines.values("inventory_id", "inventory__name")
        .annotate(
            qty_sold=Sum("qty"),
            revenue=Sum(F("qty") * F("unit_price")),
        )
        .order_by("-revenue")
    )

    context = {
        "start": start,
        "end": end,
        "summary": summary,
    }
    return render(request, "retail/reports/inventory_sales_report.html", context)

@login_required
def cash_sales_report(request):
    start = request.GET.get("start")
    end = request.GET.get("end")

    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    qs = RetailCashSale.objects.select_related("sale", "customer", "created_by")

    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    agg = qs.aggregate(
        subtotal=Sum("subtotal"),
        tax=Sum("tax"),
        total=Sum("total"),
    )

    context = {
        "start": start,
        "end": end,
        "sales": qs.order_by("created_at"),
        "totals": agg,
    }
    return render(request, "retail/reports/cash_sales_report.html", context)