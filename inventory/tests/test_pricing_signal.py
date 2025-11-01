from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from inventory.models import InventoryMaster, Inventory, Vendor
from controls.models import Measurement

class PricingSignalTests(TestCase):
    def setUp(self):
        self.unit = Measurement.objects.create(name="EA")  # adapt to your Measurement fields
        self.vend = Vendor.objects.create(name="Signal Vendor")

    def test_recompute_and_sync_pricing_creates_shadow_inventory(self):
        ipn = InventoryMaster.objects.create(
            name="Widget",
            primary_base_unit=self.unit,
            units_per_base_unit=Decimal("2.000000"),
            high_price=Decimal("10.000000"),
            retail=True,
        )
        # Signal should compute: unit_cost = 10 / 2 = 5 ; price_per_m = 5 * 1000 = 5000
        ipn.refresh_from_db()
        self.assertEqual(ipn.unit_cost, Decimal("5.000000"))
        self.assertEqual(ipn.price_per_m, Decimal("5000.000000"))

        inv = Inventory.objects.get(internal_part_number=ipn)
        # Numbers in Inventory are Decimal fields in your current model
        self.assertEqual(inv.unit_cost, Decimal("5.0000"))       # 4 dp field
        self.assertEqual(inv.price_per_m, Decimal("5000.0000"))  # 4 dp field
        self.assertEqual(inv.measurement, self.unit)
        self.assertTrue(inv.retail_item)

    def test_subsequent_update_resyncs_inventory(self):
        ipn = InventoryMaster.objects.create(
            name="Widget 2",
            primary_base_unit=self.unit,
            units_per_base_unit=Decimal("2"),
            high_price=Decimal("10"),
            retail=False,
        )
        inv = Inventory.objects.get(internal_part_number=ipn)
        # change base unit qty so costs change
        ipn.units_per_base_unit = Decimal("4")
        ipn.high_price = Decimal("12")
        ipn.retail = True
        ipn.name = "Widget 2a"
        ipn.save()

        ipn.refresh_from_db()
        self.assertEqual(ipn.unit_cost, Decimal("3.000000"))       # 12 / 4
        self.assertEqual(ipn.price_per_m, Decimal("3000.000000"))

        inv.refresh_from_db()
        self.assertEqual(inv.name, "Widget 2a")
        self.assertTrue(inv.retail_item)
        self.assertEqual(inv.unit_cost, Decimal("3.0000"))
        self.assertEqual(inv.price_per_m, Decimal("3000.0000"))