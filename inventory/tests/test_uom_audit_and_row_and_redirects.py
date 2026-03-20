from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from inventory.models import InventoryMaster, InventoryQtyVariations, Vendor
from controls.models import Measurement


class UomAuditAddRowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

        self.v = Vendor.objects.create(name="V", active=True, void=False, inventory_vendor=True)
        self.m_ea = Measurement.objects.create(name="EA")
        self.m_box = Measurement.objects.create(name="BOX")

        self.url_apply = reverse("inventory:uom_audit_apply")
        self.url_admin = reverse("inventory:uom_audit_admin")

    def _make_item(self, name="Item"):
        return InventoryMaster.objects.create(
            name=name,
            description="",
            primary_vendor=self.v,
            primary_vendor_part_number=None,
            primary_base_unit=None,
            units_per_base_unit=None,
            unit_cost=None,
            price_per_m=None,
            supplies=True,
            retail=True,
            non_inventory=False,
            online_store=True,
            not_grouped=False,
            grouped=False,
            high_price=None,
            active=True,
            retail_price=None,
            retail_markup_percent=None,
            retail_markup_flat=None,
            retail_category=None,
        )

    def test_add_uom_row_button_creates_row_without_touching_defaults_and_redirects_next(self):
        item = self._make_item("AddRow")

        next_url = self.url_admin + f"?vendor={self.v.id}&limit=25&only_issues=1"
        resp = self.client.post(
            self.url_apply,
            {
                "item_id": item.id,
                "do_add_uom": "1",
                "add_measurement": self.m_box.id,
                "add_qty": "10.0000",
                "next": next_url,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], next_url)

        item.refresh_from_db()
        qs = item.variations.all()
        self.assertEqual(qs.count(), 1)

        v = qs.first()
        self.assertEqual(v.variation_id, self.m_box.id)
        self.assertEqual(v.variation_qty, Decimal("10.0000"))
        self.assertTrue(v.active)

        # ensure it didn't set defaults/base just by adding
        self.assertFalse(v.is_base_unit)
        self.assertFalse(v.is_default_sell_uom)
        self.assertFalse(v.is_default_receive_uom)

    def test_add_uom_row_reactivates_inactive_exact_duplicate_no_new_row(self):
        item = self._make_item("Reactivate")

        existing = InventoryQtyVariations.objects.create(
            inventory=item,
            variation=self.m_box,
            variation_qty=Decimal("10.0000"),
            active=False,
            is_base_unit=False,
            is_default_sell_uom=False,
            is_default_receive_uom=False,
        )

        resp = self.client.post(
            self.url_apply,
            {
                "item_id": item.id,
                "do_add_uom": "1",
                "add_measurement": self.m_box.id,
                "add_qty": "10.0000",
            },
        )
        self.assertEqual(resp.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.variations.count(), 1)

        existing.refresh_from_db()
        self.assertTrue(existing.active, "Expected exact duplicate inactive row to be re-activated")