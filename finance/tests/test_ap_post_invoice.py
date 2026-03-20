from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import AccountsPayable
from inventory.models import Vendor


class APPostInvoiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass1234")
        self.client.login(username="testuser", password="pass1234")

        self.vendor = Vendor.objects.create(name="Test Vendor")
        self.invoice = AccountsPayable.objects.create(
            invoice_date=date(2026, 3, 20),
            vendor=self.vendor,
            invoice_number="INV-100",
            total="125.00",
            calculated_total=Decimal("125.00"),
            posted=False,
            paid=False,
        )

    def test_post_invoice_saves_payment_fields(self):
        url = reverse("finance:ap_post_invoice", kwargs={"id": self.invoice.id})
        response = self.client.post(url, {
            "paid_date": "2026-03-20",
            "method": "Check",
            "reference": "10025",
            "amount": "125.00",
            "note": "Paid in full",
        })

        self.assertEqual(response.status_code, 302)

        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.posted)
        self.assertTrue(self.invoice.paid)
        self.assertEqual(self.invoice.amount_paid, Decimal("125.00"))
        self.assertEqual(self.invoice.payment_method, "Check")
        self.assertEqual(self.invoice.check_number, "10025")
        self.assertEqual(self.invoice.payment_note, "Paid in full")

    def test_post_invoice_requires_note_if_amount_differs(self):
        url = reverse("finance:ap_post_invoice", kwargs={"id": self.invoice.id})
        response = self.client.post(url, {
            "paid_date": "2026-03-20",
            "method": "Check",
            "reference": "10025",
            "amount": "100.00",
            "note": "",
        })

        self.assertEqual(response.status_code, 302)

        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.posted)
        self.assertFalse(self.invoice.paid)