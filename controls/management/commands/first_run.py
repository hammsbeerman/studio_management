import os
from decimal import Decimal
from typing import Iterable

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from weasyprint import HTML

from finance.models import Krueger_Araging
from finance.helpers_statements import (
    get_live_statement_queryset,
    build_customer_statement_data,
)

JOB_STATUSES: Iterable[str] = (
    "Open",
    "Quoted",
    "In Progress",
    "Waiting on Customer",
    "Waiting on Vendor",
    "Order Out",
    "Ready for Pickup",
    "Completed",
    "Billed",
    "Void",
)

# Prefer stable IDs so legacy code that used pk=1/2 keeps working.
NUMBERING_SEEDS = [
    {"id": 1, "name": "Workorder Number", "prefix": "WO", "padding": 5, "start": 1},
    {"id": 2, "name": "Customer Number",  "prefix": "C",  "padding": 5, "start": 1},
    {"id": 3, "name": "Quote Number",     "prefix": "Q",  "padding": 5, "start": 1},
]

# Add/trim as you like; this tolerates models that only have `name`.
MEASUREMENTS = [
    {"name": "Each",   "abbr": "ea",  "type": "count"},
    {"name": "Sheet",  "abbr": "sht", "type": "count"},
    {"name": "Pack",   "abbr": "pk",  "type": "count"},
    {"name": "Box",    "abbr": "box", "type": "count"},
    {"name": "Inch",   "abbr": "in",  "type": "length"},
    {"name": "Foot",   "abbr": "ft",  "type": "length"},
    {"name": "Yard",   "abbr": "yd",  "type": "length"},
    {"name": "Millimeter", "abbr": "mm", "type": "length"},
    {"name": "Centimeter", "abbr": "cm", "type": "length"},
    {"name": "Meter",  "abbr": "m",   "type": "length"},
    {"name": "Square Foot", "abbr": "sqft", "type": "area"},
    {"name": "Square Meter","abbr": "sqm",  "type": "area"},
]

def _field_set(Model):
    return {
        f.name for f in Model._meta.get_fields()
        if getattr(f, "concrete", False) and not getattr(f, "auto_created", False)
    }

class Command(BaseCommand):
    help = "Generate bulk customer statements as PDF"

    def handle(self, *args, **kwargs):
        ZERO = Decimal("0.00")

        # Default behavior matches old bulk statement flow:
        # include everything except LK Design
        effective_companies = ["Krueger Printing", "Office Supplies"]

        # Only include customers that are actually on the snapshot-backed
        # Krueger statements list and still have a positive total.
        customer_ids = list(
            Krueger_Araging.objects
            .exclude(total__isnull=True)
            .exclude(total__lte=0)
            .values_list("customer_id", flat=True)
        )

        if not customer_ids:
            self.stdout.write("No customers with statement balances found.")
            return

        qs = (
            get_live_statement_queryset()
            .filter(customer_id__in=customer_ids)
            .order_by("customer__company_name", "date_billed", "workorder")
        )

        customer_data = build_customer_statement_data(qs)

        # Extra safety: keep only customers with positive live totals
        customer_data = [
            row for row in customer_data
            if (row.get("total_open_balance", {}).get("open_balance__sum") or ZERO) > ZERO
        ]

        if not customer_data:
            self.stdout.write("No live statement data found for customers in Krueger_Araging.")
            return

        context = {
            "customer_data": customer_data,
            "date": timezone.now().date(),
            "todays_date": timezone.now(),
            "effective_companies": effective_companies,
        }

        html_string = render_to_string(
            "pdf/weasyprint/krueger_statement_bulk.html",
            context,
        )

        base_url = getattr(settings, "SITE_URL", None) or settings.BASE_DIR
        html = HTML(string=html_string, base_url=base_url)
        pdf_bytes = html.write_pdf()

        save_dir = os.path.join(settings.MEDIA_ROOT, "statements")
        os.makedirs(save_dir, exist_ok=True)

        base_name = timezone.now().date().strftime("%Y_%B_%d")
        filename = f"{base_name}.pdf"
        filepath = os.path.join(save_dir, filename)

        counter = 1
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}.pdf"
            filepath = os.path.join(save_dir, filename)
            counter += 1

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        self.stdout.write(
            self.style.SUCCESS(
                f"PDF saved to {filepath} ({len(customer_data)} customers)"
            )
        )