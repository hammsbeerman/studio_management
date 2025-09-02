import os, datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML
from customers.models import Customer, Contact
from finance.models import Krueger_Araging
from workorders.models import WorkorderItem, Workorder
from finance.models import Krueger_Araging
from django.db.models import Sum

class Command(BaseCommand):
    help = "Generate bulk customer statements as PDF"

    def handle(self, *args, **kwargs):
        customers = Customer.objects.filter(
            id__in=Krueger_Araging.objects.values('customer')
        ).order_by('company_name')

        customer_data = []
        for customer in customers:
            workorders = Workorder.objects.filter(customer=customer.id)\
                .exclude(internal_company='LK Design')\
                .exclude(billed=0)\
                .exclude(paid_in_full=1)\
                .exclude(quote=1)\
                .exclude(void=1)\
                .exclude(workorder_total=0)\
                .order_by('workorder')

            total_open_balance = workorders.aggregate(Sum('open_balance'))

            if workorders.exists():
                customer_data.append({
                    'customer': customer,
                    'workorders': workorders,
                    'total_open_balance': total_open_balance,
                })

        context = {
            'customer_data': customer_data,
            'date': datetime.date.today(),
            'todays_date': timezone.now(),
        }

        html_string = render_to_string(
            'pdf/weasyprint/krueger_statement_bulk.html',
            context
        )
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        print("PDF length:", len(pdf_bytes))

        SAVE_DIR = os.path.join(settings.MEDIA_ROOT, "statements")

        os.makedirs(SAVE_DIR, exist_ok=True)

        # Base name like "August_2025"
        base_name = datetime.date.today().strftime("%Y_%B_%d")
        filename = f"{base_name}.pdf"
        filepath = os.path.join(SAVE_DIR, filename)

        # If file exists, add a counter suffix
        counter = 1
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}.pdf"
            filepath = os.path.join(SAVE_DIR, filename)
            counter += 1

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        self.stdout.write(self.style.SUCCESS(f"PDF saved to {filepath}"))
