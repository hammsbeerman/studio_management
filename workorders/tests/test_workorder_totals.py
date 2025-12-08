from decimal import Decimal

from django.test import TestCase

from customers.models import Customer
from workorders.models import Workorder, WorkorderItem
from inventory.models import RetailWorkorderItem
from workorders.services.totals import compute_workorder_totals


class WorkorderTotalsTests(TestCase):
    _wo_counter = 1000

    def _make_customer(self, **overrides):
        """
        Minimal customer factory that satisfies non-null fields.
        """
        data = {
            "company_name": "Test Customer",
            "first_name": "",
            "last_name": "",
            "address1": "",
            "city": "",
            "state": "",
            "zipcode": "",
            "phone1": "",
            "phone2": "",
            "email": "",
            "website": "",
            "po_number": "",
            "customer_number": "TEST",
            "avg_days_to_pay": "",
            "mail_bounced_back": False,
            "tax_exempt": False,
        }
        data.update(overrides)
        return Customer.objects.create(**data)

    def _make_workorder(self, customer, **overrides):
        """
        Minimal workorder factory that matches your model constraints.
        """
        type(self)._wo_counter += 1
        data = {
            "customer": customer,
            "workorder": f"WO-{type(self)._wo_counter}",
            "internal_company": "Krueger Printing",
            "quote": "0",  # '0' = Workorder, not Quote
            "notes": "",
            "tax_exempt": False,
        }
        data.update(overrides)
        return Workorder.objects.create(**data)

    def test_regular_items_only_totals_match_sum_of_items(self):
        """
        Non-POS path: totals are based on billable, non-parent WorkorderItem.absolute_price + tax_amount.
        """
        cust = self._make_customer()
        wo = self._make_workorder(cust)

        # two billable non-parent items
        WorkorderItem.objects.create(
            workorder=wo,
            workorder_hr=wo.workorder,
            description="Item 1",
            absolute_price=Decimal("100.00"),
            tax_amount=Decimal("5.00"),
            total_with_tax=Decimal("105.00"),
            billable=True,
            parent=False,
        )
        WorkorderItem.objects.create(
            workorder=wo,
            workorder_hr=wo.workorder,
            description="Item 2",
            absolute_price=Decimal("50.00"),
            tax_amount=Decimal("2.50"),
            total_with_tax=Decimal("52.50"),
            billable=True,
            parent=False,
        )
        # one non-billable that should be ignored
        WorkorderItem.objects.create(
            workorder=wo,
            workorder_hr=wo.workorder,
            description="Non-billable",
            absolute_price=Decimal("999.00"),
            tax_amount=Decimal("99.00"),
            total_with_tax=Decimal("1098.00"),
            billable=False,
            parent=False,
        )

        totals = compute_workorder_totals(wo)

        self.assertEqual(totals.wi_subtotal, Decimal("150.00"))
        self.assertEqual(totals.wi_tax, Decimal("7.50"))
        self.assertEqual(totals.subtotal, Decimal("150.00"))
        self.assertEqual(totals.tax, Decimal("7.50"))
        self.assertEqual(totals.total, Decimal("157.50"))

    def test_pos_items_tax_applied_when_not_tax_exempt(self):
        """
        POS path: RetailWorkorderItem.total_price is summed, tax is 5.5% if not tax-exempt.
        """
        cust = self._make_customer(tax_exempt=False)
        wo = self._make_workorder(cust, tax_exempt=False)

        # no regular WorkorderItem rows for this test
        RetailWorkorderItem.objects.create(
            workorder=wo,
            customer=cust,
            description="POS 1",
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )
        RetailWorkorderItem.objects.create(
            workorder=wo,
            customer=cust,
            description="POS 2",
            quantity=Decimal("1"),
            unit_price=Decimal("5.00"),
            total_price=Decimal("5.00"),
        )

        totals = compute_workorder_totals(wo)

        # pos_subtotal = 15.00, pos_tax = 15.00 * 0.055 = 0.825 -> 0.83
        self.assertEqual(totals.pos_subtotal, Decimal("15.00"))
        self.assertEqual(totals.pos_tax, Decimal("0.82"))
        self.assertEqual(totals.subtotal, Decimal("15.00"))
        self.assertEqual(totals.tax, Decimal("0.82"))
        self.assertEqual(totals.total, Decimal("15.82"))

    def test_pos_items_tax_zero_when_workorder_or_customer_tax_exempt(self):
        """
        Tax should be 0.00 if either:
        - workorder.tax_exempt is True, OR
        - customer.tax_exempt is True
        """

        # Case 1: workorder tax_exempt True
        cust1 = self._make_customer(tax_exempt=False)
        wo1 = self._make_workorder(cust1, tax_exempt=True)
        RetailWorkorderItem.objects.create(
            workorder=wo1,
            customer=cust1,
            description="POS",
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )
        totals1 = compute_workorder_totals(wo1)
        self.assertEqual(totals1.pos_subtotal, Decimal("10.00"))
        self.assertEqual(totals1.pos_tax, Decimal("0.00"))
        self.assertEqual(totals1.tax, Decimal("0.00"))
        self.assertEqual(totals1.total, Decimal("10.00"))

        # Case 2: customer tax_exempt True overrides workorder False
        cust2 = self._make_customer(tax_exempt=True)
        wo2 = self._make_workorder(cust2, tax_exempt=False)
        RetailWorkorderItem.objects.create(
            workorder=wo2,
            customer=cust2,
            description="POS",
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )
        totals2 = compute_workorder_totals(wo2)
        self.assertEqual(totals2.pos_subtotal, Decimal("10.00"))
        self.assertEqual(totals2.pos_tax, Decimal("0.00"))
        self.assertEqual(totals2.tax, Decimal("0.00"))
        self.assertEqual(totals2.total, Decimal("10.00"))