import datetime
import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from weasyprint import HTML

from finance.helpers_statements import (
    get_live_statement_queryset,
    build_customer_statement_data,
)


class Command(BaseCommand):
    help = "Generate bulk customer statements as PDF"

    def handle(self, *args, **kwargs):
        ZERO = Decimal("0.00")

        # Default behavior matches old bulk statement flow:
        # include everything except LK Design
        effective_companies = ["Krueger Printing", "Office Supplies"]

        qs = (
            get_live_statement_queryset()
            .order_by("customer__company_name", "date_billed", "workorder")
        )

        customer_data = build_customer_statement_data(qs)

        # Extra safety: keep only customers with positive balances
        customer_data = [
            row for row in customer_data
            if (row.get("total_open_balance", {}).get("open_balance__sum") or ZERO) > ZERO
        ]

        if not customer_data:
            self.stdout.write("No customers with statement balances found.")
            return

        self.stdout.write(f"Generating statements for {len(customer_data)} customers...")

        context = {
            "customer_data": customer_data,
            "date": datetime.date.today(),
            "todays_date": timezone.now(),
            "effective_companies": effective_companies,
        }

        html_string = render_to_string(
            "pdf/weasyprint/krueger_statement_bulk.html",
            context,
        )

        base_url = getattr(settings, "SITE_URL", None)
        if not base_url:
            base_url = settings.BASE_DIR

        html = HTML(string=html_string, base_url=base_url)

        self.stdout.write("Rendering PDF...")
        pdf_bytes = html.write_pdf()

        save_dir = os.path.join(settings.MEDIA_ROOT, "statements")
        os.makedirs(save_dir, exist_ok=True)

        base_name = datetime.date.today().strftime("%Y_%B_%d")
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