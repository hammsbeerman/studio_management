from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from inventory.models import InventoryMaster, InventoryQtyVariations, InventoryLedger
from controls.models import Measurement


class UomAuditApplyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

        self.url_apply = reverse("inventory:uom_audit_apply")
        self.url_admin = reverse("inventory:uom_audit_admin")

        # sanity: prove we're not bouncing to login
        resp = self.client.get(self.url_admin)
        self.assertNotEqual(resp.status_code, 302, "Expected logged-in user to access uom_audit_admin without redirect")

        self.m_ea = Measurement.objects.create(name="EA")
        self.m_box = Measurement.objects.create(name="BOX")
        self.m_case = Measurement.objects.create(name="CASE")

    def _make_item(self, name="Test Item", non_inventory=False, active=True):
        return InventoryMaster.objects.create(
            name=name,
            description="",
            primary_vendor=None,
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

    def _add_ledger(self, item):
        return InventoryLedger.objects.create(
            inventory_item=item,
            qty_delta=Decimal("1.0000"),
            source_type="ADJUSTMENT",
            source_id="T1",
            note="test",
        )

    def test_apply_sets_base_sell_receive_and_creates_missing_variations(self):
        item = self._make_item("Apply Item", non_inventory=False)

        resp = self.client.post(
            self.url_apply,
            {
                "item_id": item.id,
                "base_measurement": self.m_ea.id,
                "sell_measurement": self.m_box.id,
                "sell_qty": "10.0000",
                "receive_measurement": self.m_case.id,
                "receive_qty": "100.0000",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.url_admin)

        item.refresh_from_db()
        qs = item.variations.all()

        base = qs.filter(is_base_unit=True, active=True).first()
        self.assertIsNotNone(base)
        self.assertEqual(base.variation_id, self.m_ea.id)
        self.assertEqual(base.variation_qty, Decimal("1.0000"))

        sell = qs.filter(is_default_sell_uom=True, active=True).first()
        self.assertIsNotNone(sell)
        self.assertEqual(sell.variation_id, self.m_box.id)
        self.assertEqual(sell.variation_qty, Decimal("10.0000"))

        recv = qs.filter(is_default_receive_uom=True, active=True).first()
        self.assertIsNotNone(recv)
        self.assertEqual(recv.variation_id, self.m_case.id)
        self.assertEqual(recv.variation_qty, Decimal("100.0000"))

    def test_apply_mark_non_inventory_sets_flag_when_no_ledger(self):
        item = self._make_item("NI Allowed", non_inventory=False)

        resp = self.client.post(
            self.url_apply,
            {"item_id": item.id, "mark_non_inventory": "on"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.url_admin)

        item.refresh_from_db()
        self.assertTrue(item.non_inventory)

    def test_guardrail_blocks_mark_non_inventory_when_ledger_exists(self):
        item = self._make_item("NI Blocked", non_inventory=False)
        self._add_ledger(item)

        resp = self.client.post(
            self.url_apply,
            {"item_id": item.id, "mark_non_inventory": "on"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.url_admin)

        item.refresh_from_db()
        self.assertFalse(item.non_inventory)

    def test_guardrail_blocks_base_change_when_ledger_exists(self):
        item = self._make_item("Base Blocked", non_inventory=False)

        InventoryQtyVariations.objects.create(
            inventory=item,
            variation=self.m_ea,
            variation_qty=Decimal("1.0000"),
            is_base_unit=True,
            active=True,
        )

        self._add_ledger(item)

        resp = self.client.post(
            self.url_apply,
            {"item_id": item.id, "base_measurement": self.m_box.id},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.url_admin)

        item.refresh_from_db()
        base = item.variations.filter(is_base_unit=True, active=True).first()
        self.assertIsNotNone(base)
        self.assertEqual(base.variation_id, self.m_ea.id)

    def test_invalid_qty_rejected(self):
        item = self._make_item("Bad Qty", non_inventory=False)

        resp = self.client.post(
            self.url_apply,
            {
                "item_id": item.id,
                "sell_measurement": self.m_box.id,
                "sell_qty": "not-a-number",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.url_admin)

        self.assertEqual(item.variations.count(), 0)
