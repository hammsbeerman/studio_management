import os
import tempfile

from celery import shared_task
from django.conf import settings
from django.core.files.base import File
from django.template.loader import render_to_string
from django.utils import timezone

from weasyprint import HTML

from .helpers_statements import VALID_COMPANIES, build_customer_statement_data, get_live_statement_queryset
from .models import StatementRun


@shared_task
def build_krueger_bulk_statements(run_id):
    run = StatementRun.objects.get(pk=run_id)
    run.status = "running"
    run.started_at = timezone.now()
    run.error = ""
    run.save(update_fields=["status", "started_at", "error"])

    final_tmp_path = None

    try:
        filters = run.filters_json or {}
        selected_companies = [
            c for c in (filters.get("companies") or [])
            if c in VALID_COMPANIES
        ]
        effective_companies = selected_companies if selected_companies else ["Krueger Printing"]
        customer_id = filters.get("customer_id") or None

        qs = (
            get_live_statement_queryset(companies=effective_companies, customer=customer_id)
            .order_by("customer__company_name", "date_billed", "workorder")
        )

        customer_data = build_customer_statement_data(qs)
        customer_data = [
            row for row in customer_data
            if (row.get("total_open_balance", {}).get("open_balance__sum") or 0) > 0
        ]

        html_string = render_to_string(
            "pdf/weasyprint/krueger_statement_bulk.html",
            {
                "customer_data": customer_data,
                "todays_date": timezone.now(),
                "date": timezone.now().date(),
                "selected_companies": selected_companies,
                "effective_companies": effective_companies,
            },
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
            final_tmp_path = output.name

        base_url = getattr(settings, "WEASYPRINT_BASEURL", None) or str(settings.BASE_DIR)
        HTML(string=html_string, base_url=base_url).write_pdf(final_tmp_path)

        filename = f"krueger_bulk_statements_{run.pk}.pdf"
        with open(final_tmp_path, "rb") as f:
            run.file.save(filename, File(f), save=False)

        run.status = "complete"
        run.completed_at = timezone.now()
        run.save(update_fields=["file", "status", "completed_at"])

    except Exception as exc:
        run.status = "failed"
        run.completed_at = timezone.now()
        run.error = str(exc)
        run.save(update_fields=["status", "completed_at", "error"])
        raise

    finally:
        if final_tmp_path and os.path.exists(final_tmp_path):
            try:
                os.unlink(final_tmp_path)
            except Exception:
                pass
