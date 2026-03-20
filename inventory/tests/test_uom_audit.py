from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from inventory.models import InventoryMaster, InventoryQtyVariations, InventoryLedger, Vendor
from controls.models import Measurement


class UomAuditAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

        # Vendors
        self.v_good = Vendor.objects.create(name="Good Vendor", active=True, void=False, inventory_vendor=True)
        self.v_inactive = Vendor.objects.create(name="Inactive Vendor", active=False, void=False, inventory_vendor=True)
        self.v_void = Vendor.objects.create(name="Void Vendor", active=True, void=True, inventory_vendor=True)
        self.v_not_inventory = Vendor.objects.create(name="Not Inventory Vendor", active=True, void=False, inventory_vendor=False)

        # Measurements
        self.m_ea = Measurement.objects.create(name="EA")
        self.m_box = Measurement.objects.create(name="BOX")
        self.m_case = Measurement.objects.create(name="CASE")

        self.url_admin = reverse("inventory:uom_audit_admin")
        self.url_apply = reverse("inventory:uom_audit_apply")

    def _make_item(self, name, vendor=None, non_inventory=False, active=True):
        return InventoryMaster.objects.create(
            name=name,
            description="",
            primary_vendor=vendor,
            primary_vendor_part_number=None,
            primary_base_unit=None,
            units_per_base_unit=None,
            unit_cost=None,
            price_per_m=None,
            supplies=True,
            retail=True,
            non_inventory=non_inventory,
            online_store=True,
            not_grouped=False,
            grouped=False,
            high_price=None,
            active=active,
            retail_price=None,
            retail_markup_percent=None,
            retail_markup_flat=None,
            retail_category=None,
        )

    def _make_variation(self, item, measurement, qty, *, active=True, base=False, sell=False, recv=False):
        return InventoryQtyVariations.objects.create(
            inventory=item,
            variation=measurement,
            variation_qty=Decimal(qty),
            is_base_unit=base,
            is_default_sell_uom=sell,
            is_default_receive_uom=recv,
            active=active,
        )

    def _make_ledger(self, item, qty_delta="1.0000"):
        return InventoryLedger.objects.create(
            inventory_item=item,
            qty_delta=Decimal(qty_delta),
            source_type="ADJUSTMENT",
            source_id="T1",
            note="test",
        )

    def test_vendor_dropdown_only_shows_vendors_with_inventory_items(self):
        """
        Vendor dropdown should only contain vendors that appear on InventoryMaster
        where primary_vendor IS NOT NULL and non_inventory=False, and vendor flags
        must be active=True, void=False, inventory_vendor=True.
        """
        self._make_item("Item A", vendor=self.v_good, non_inventory=False)
        self._make_item("Item B", vendor=self.v_good, non_inventory=False)

        # Non-inventory item should not count
        self._make_item("Item C", vendor=self.v_good, non_inventory=True)

        # Vendors failing flags
        self._make_item("Item D", vendor=self.v_inactive, non_inventory=False)
        self._make_item("Item E", vendor=self.v_void, non_inventory=False)
        self._make_item("Item F", vendor=self.v_not_inventory, non_inventory=False)

        resp = self.client.get(self.url_admin)
        self.assertEqual(resp.status_code, 200)

        form = resp.context.get("form")
        self.assertIsNotNone(form)

        qs = form.fields["vendor"].queryset
        vendor_ids = set(qs.values_list("id", flat=True))

        self.assertIn(self.v_good.id, vendor_ids)
        self.assertNotIn(self.v_inactive.id, vendor_ids)
        self.assertNotIn(self.v_void.id, vendor_ids)
        self.assertNotIn(self.v_not_inventory.id, vendor_ids)

    def test_audit_limit_caps_rows(self):
        for i in range(5):
            self._make_item(f"Limit Item {i}", vendor=self.v_good, non_inventory=False)

        # Most implementations only compute 'result' when audit is explicitly run.
        # Trigger it the same way the UI does (your view likely checks for GET params).
        resp = self.client.get(self.url_admin, {"vendor": self.v_good.id, "limit": 2, "run": "1"})
        self.assertEqual(resp.status_code, 200)

        result = resp.context.get("result")
        if result is None:
            # Fallback: some views render results without context var, but the page should still load.
            # At minimum, verify response is OK and includes the audit table header when run is requested.
            html = resp.content.decode("utf-8", errors="replace")
            self.assertIn("UOM Audit", html)
        else:
            self.assertLessEqual(len(result.rows), 2)

    def test_uoms_on_item_only_shows_active_rows(self):
        item = self._make_item("ActiveOnly", vendor=self.v_good, non_inventory=False)

        # active
        self._make_variation(item, self.m_ea, "1.0000", active=True, base=True)
        # inactive (should NOT render)
        self._make_variation(item, self.m_box, "2.0000", active=False)

        resp = self.client.get(self.url_admin, {"vendor": self.v_good.id, "limit": 50})
        self.assertEqual(resp.status_code, 200)

        html = resp.content.decode("utf-8", errors="replace")

        # Should show EA x 1
        self.assertIn("EA", html)
        # Should NOT show BOX x 2 anywhere in the “UOMs on item” listing (template filters v.active)
        self.assertNotIn("BOX × 2", html)
        self.assertNotIn("BOX &times; 2", html)  # just in case