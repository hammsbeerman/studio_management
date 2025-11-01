from django.apps import apps
from django.test import TestCase

from inventory.models import InventoryMaster

class PurchaseHistoryTests(TestCase):
    def setUp(self):
        self.ipn = InventoryMaster.objects.create(name="Roll Media")

    def test_purchase_history_ordering(self):
        InvoiceItem = apps.get_model("finance", "InvoiceItem")
        Invoice = apps.get_model("finance", "AccountsPayable")
        Vendor = apps.get_model("inventory", "Vendor")

        if not InvoiceItem or not Invoice:
            self.skipTest("finance.InvoiceItem/Invoice not installed")

        vend = Vendor.objects.create(name="Vend A")
        inv1 = Invoice.objects.create(vendor=vend, invoice_date="2024-01-01")
        inv2 = Invoice.objects.create(vendor=vend, invoice_date="2024-03-01")
        inv3 = Invoice.objects.create(vendor=vend, invoice_date="2024-02-01")

        InvoiceItem.objects.create(invoice=inv1, internal_part_number=self.ipn, unit_cost=1)
        InvoiceItem.objects.create(invoice=inv2, internal_part_number=self.ipn, unit_cost=2)
        InvoiceItem.objects.create(invoice=inv3, internal_part_number=self.ipn, unit_cost=3)

        rows = list(self.ipn.purchase_history())
        dates = [r.invoice.invoice_date for r in rows]
        self.assertEqual(dates, sorted(dates, reverse=True))