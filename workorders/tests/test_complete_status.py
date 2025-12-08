from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from customers.models import Customer
from workorders.models import Workorder, WorkorderItem
from workorders.services.totals import compute_workorder_totals


User = get_user_model()


class CompleteStatusTests(TestCase):
    def setUp(self):
        # Simple user to satisfy @login_required
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="password123",
        )
        self.client.login(username="tester", password="password123")

        # Minimal customer
        self.customer = Customer.objects.create(
            company_name="Test Customer",
            first_name="Test",
            last_name="Customer",
            address1="123 Main",
            city="Reedsburg",
            state="WI",
            zipcode="53959",
            phone1="",
            phone2="",
            email="",
            website="",
            open_balance=None,
            high_balance=None,
        )

        # Workorder header (not completed yet)
        self.workorder = Workorder.objects.create(
            customer=self.customer,
            ship_to=None,
            hr_customer="Test Customer",
            workorder="1001",
            internal_company="Office Supplies",
            quote="0",
            description="Test WO for complete_status",
            tax_exempt=False,
            tax="0",
            subtotal="0",
            workorder_total="0",
            completed=False,
            total_balance=Decimal("0"),
            amount_paid=Decimal("0"),
            open_balance=Decimal("0"),
            paid_in_full=False,
        )

        # One simple billable line item
        WorkorderItem.objects.create(
            workorder=self.workorder,
            workorder_hr=self.workorder.workorder,
            item_category=None,
            item_subcategory=None,
            setprice_category=None,
            setprice_item=None,
            pricesheet_modified=False,
            design_type=None,
            postage_type=None,
            description="Test line",
            item_order=1,
            quantity=Decimal("1"),
            show_qty_on_wo=True,
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
            override_price=None,
            absolute_price=Decimal("100.00"),
            billable=True,
            notes="",
            show_notes=False,
            internal_company="Office Supplies",
            tax_exempt=False,
            tax_amount=Decimal("5.50"),
            total_with_tax=Decimal("105.50"),
            prequoted=False,
            quoted_amount=None,
            parent_item=None,
            added_to_parent=False,
            parent=False,
            child=False,
            job_status=None,
            completed=False,
        )

    def test_complete_status_completes_workorder_and_updates_customer_balances(self):
        """
        Calling complete_status on an open workorder should:
        - flip completed to True
        - set WO subtotal/tax/total_balance/open_balance from compute_workorder_totals
        - update customer.open_balance / high_balance
        """
        url = reverse("workorders:complete_status")
        resp = self.client.get(url, {"workorder": self.workorder.id})

        # Expect redirect back to overview
        self.assertEqual(resp.status_code, 302)

        self.workorder.refresh_from_db()
        self.customer.refresh_from_db()

        totals = compute_workorder_totals(self.workorder)

        # Workorder flags / header fields
        self.assertTrue(self.workorder.completed)
        self.assertEqual(self.workorder.total_balance, totals.total)
        self.assertEqual(self.workorder.open_balance, totals.total)

        # subtotal/tax are stored as strings on the model
        self.assertEqual(
            Decimal(str(self.workorder.subtotal or "0")),
            totals.subtotal.quantize(Decimal("0.01")),
        )
        self.assertEqual(
            Decimal(str(self.workorder.tax or "0")),
            totals.tax.quantize(Decimal("0.01")),
        )

        # Customer balances reflect this workorder
        self.assertIsNotNone(self.customer.open_balance)
        self.assertIsNotNone(self.customer.high_balance)
        self.assertEqual(
            self.customer.open_balance.quantize(Decimal("0.01")),
            totals.total.quantize(Decimal("0.01")),
        )
        self.assertGreaterEqual(self.customer.high_balance, self.customer.open_balance)