from decimal import Decimal

from django.test import TestCase

from inventory.models import InventoryMaster, Inventory, InventoryRetailPrice
from inventory.services.pricing import (
    ensure_retail_pricing,
    get_effective_retail_price,
    compute_retail_price,
)


class InventoryRetailPricingTests(TestCase):
    def setUp(self):
        self.item = InventoryMaster.objects.create(
            name="Widget",
            unit_cost=Decimal("10.00"),
            retail_markup_percent=Decimal("50.00"),  # 50% over cost
            non_inventory=False,                     # ✅ REQUIRED
            supplies=True,                           # (has default, but explicit is fine)
            retail=True,                             # (has default, but explicit is fine)
        )

    def test_ensure_retail_pricing_sets_purchase_and_calculated(self):
        rp = ensure_retail_pricing(self.item)

        self.assertEqual(rp.purchase_price, Decimal("10.00"))
        self.assertEqual(rp.calculated_price, compute_retail_price(self.item))
        self.assertIsNone(rp.override_price)

    def test_get_effective_price_respects_override(self):
        rp = ensure_retail_pricing(self.item)
        base_price = get_effective_retail_price(self.item)
        self.assertEqual(base_price, compute_retail_price(self.item))

        rp.override_price = Decimal("13.00")
        rp.save()

        effective = get_effective_retail_price(self.item)
        self.assertEqual(effective, Decimal("13.00"))

    def test_inventory_add_resets_override_and_recomputes(self):
        rp = ensure_retail_pricing(self.item)
        rp.override_price = Decimal("12.00")
        rp.save()

        # New stock received for this item
        Inventory.objects.create(
            name="Widget shipment",
            internal_part_number=self.item,
        )

        rp.refresh_from_db()
        self.assertIsNone(rp.override_price)
        self.assertEqual(rp.calculated_price, compute_retail_price(self.item))