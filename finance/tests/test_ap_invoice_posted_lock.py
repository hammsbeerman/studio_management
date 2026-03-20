from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import AccountsPayable, InvoiceItem
from inventory.models import Vendor, InventoryMaster, VendorItemDetail


class APInvoicePostedLockTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass1234")
        self.client.login(username="testuser", password="pass1234")

        self.vendor = Vendor.objects.create(name="Test Vendor")
        self.inventory_item = InventoryMaster.objects.create(
            name="Paper",
            non_inventory=False,
        )

        VendorItemDetail.objects.create(
            vendor=self.vendor,
            internal_part_number=self.inventory_item,
            supplies=True,
            retail=True,
            non_inventory=False,
            online_store=True,
        )

        self.invoice = AccountsPayable.objects.create(
            invoice_date=date(2026, 3, 20),
            vendor=self.vendor,
            invoice_number="INV-200",
            total="50.00",
            calculated_total=Decimal("50.00"),
            posted=True,
        )

        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            vendor=self.vendor,
            internal_part_number=self.inventory_item,
            name="Paper",
            invoice_qty=Decimal("1.00"),
            qty=Decimal("1.00"),
            invoice_unit_cost=Decimal("50.00"),
            unit_cost=Decimal("50.00"),
            line_total=Decimal("50.00"),
        )

    def test_posted_invoice_blocks_edit_invoice_item_post(self):
        url = reverse("finance:ap_edit_invoice_item_invoice", kwargs={"invoice": self.invoice.id, "id": self.item.id})
        response = self.client.post(url, {
            "invoice": self.invoice.id,
            "name": "Paper Changed",
            "invoice_qty": "2",
            "invoice_unit_cost": "25.00",
            "internal_part_number": self.inventory_item.id,
        })

        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Paper")
        self.assertEqual(self.item.invoice_qty, Decimal("1.00"))