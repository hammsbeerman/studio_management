from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


from controls.models import Measurement
from finance.models import AccountsPayable, InvoiceItem
from inventory.models import Vendor, InventoryMaster, InventoryQtyVariations, VendorItemDetail


class APInvoiceDetailUomTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

        self.vendor = Vendor.objects.create(name="Test Vendor")

        self.invoice = AccountsPayable.objects.create(
            invoice_date=date.today(),
            vendor=self.vendor,
            invoice_number="INV-1",
            check_number="",   # required field (null=False) but blank allowed
            total="0",
        )

        self.item = InventoryMaster.objects.create(
            name="Test Item",
            non_inventory=False,
        )

        # Needed because finance.models.highprice_handler expects this to exist
        VendorItemDetail.objects.create(
            vendor=self.vendor,
            internal_part_number=self.item,
            name=self.item.name,
            vendor_part_number="",
            description="",
            supplies=True,
            retail=True,
            non_inventory=False,
            online_store=True,
            high_price=None,
        )

        self.m_box = Measurement.objects.create(name="BOX")

        self.url = reverse("finance:ap_invoice_detail_id", kwargs={"id": self.invoice.id})

        

    def _post_line(self, extra):
        """
        Minimal POST payload to create an InvoiceItem through invoice_detail().
        """
        payload = {
            # ModelForm fields
            "name": "Line 1",
            "vendor_part_number": "",
            "description": "",
            "internal_part_number": str(self.item.id),
            "vendor": str(self.vendor.id),
            "invoice_unit_cost": "100.00",
            "invoice_qty": "2",

            # invoice_detail extras
            "ppm": "0",
        }
        payload.update(extra)
        return self.client.post(self.url, payload)

    def test_creates_variation_for_unit_and_qty_and_sets_invoice_unit(self):
        resp = self._post_line(
            {
                "unit": str(self.m_box.id),
                "variation_qty": "10",   # BOX x 10
            }
        )
        self.assertEqual(resp.status_code, 302)

        # Variation created (or reused) for (item, BOX, 10)
        vqs = InventoryQtyVariations.objects.filter(
            inventory=self.item,
            variation=self.m_box,
            variation_qty=Decimal("10"),
        )
        self.assertEqual(vqs.count(), 1)
        v = vqs.first()
        self.assertTrue(v.active)

        # InvoiceItem points at that variation
        inv_item = InvoiceItem.objects.filter(invoice=self.invoice).order_by("-id").first()
        self.assertIsNotNone(inv_item)
        self.assertEqual(inv_item.invoice_unit_id, v.id)

    def test_reuses_same_measurement_and_qty_no_duplicates(self):
        # First post creates it
        self._post_line({"unit": str(self.m_box.id), "variation_qty": "10"})
        # Second post should reuse exact match
        self._post_line({"name": "Line 2", "unit": str(self.m_box.id), "variation_qty": "10"})

        vqs = InventoryQtyVariations.objects.filter(
            inventory=self.item,
            variation=self.m_box,
            variation_qty=Decimal("10"),
        )
        self.assertEqual(vqs.count(), 1, "Should not create duplicate UOM rows for same measurement+qty")

    def test_reactivates_inactive_exact_duplicate(self):
        v = InventoryQtyVariations.objects.create(
            inventory=self.item,
            variation=self.m_box,
            variation_qty=Decimal("10"),
            active=False,
        )

        resp = self._post_line({"unit": str(self.m_box.id), "variation_qty": "10"})
        self.assertEqual(resp.status_code, 302)

        v.refresh_from_db()
        self.assertTrue(v.active, "Exact duplicate inactive row should be reactivated, not recreated")

        vqs = InventoryQtyVariations.objects.filter(
            inventory=self.item,
            variation=self.m_box,
            variation_qty=Decimal("10"),
        )
        self.assertEqual(vqs.count(), 1)