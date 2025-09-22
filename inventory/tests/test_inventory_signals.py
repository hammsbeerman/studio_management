from decimal import Decimal
from django.test import TestCase
from inventory.models import InventoryMaster, Inventory
from controls.models import Measurement

class InventorySignalsTests(TestCase):
    def setUp(self):
        self.unit = Measurement.objects.create(name="Each")

    def test_unit_cost_handler_sets_costs(self):
        # high_price / units_per_base_unit = unit_cost ; price_per_m = unit_cost * 1000
        master = InventoryMaster.objects.create(
            name="Paper",
            primary_base_unit=self.unit,
            units_per_base_unit=Decimal("1000"),
            high_price=Decimal("2.50"),
        )
        master.refresh_from_db()
        self.assertEqual(master.unit_cost, Decimal("0.0025"))
        self.assertEqual(master.price_per_m, Decimal("2.5"))

    def test_inventory_master_handler_creates_inventory_row(self):
        master = InventoryMaster.objects.create(name="Vinyl", primary_base_unit=self.unit)
        inv_qs = Inventory.objects.filter(internal_part_number=master)
        self.assertTrue(inv_qs.exists(), "Signal should create an Inventory row")
        self.assertEqual(inv_qs.first().name, "Vinyl")

    def test_inventory_master_handler_is_idempotent(self):
        master = InventoryMaster.objects.create(name="Banner", primary_base_unit=self.unit)
        # simulate a second save (should not create a duplicate Inventory row)
        master.name = "Banner Updated"
        master.save()
        self.assertEqual(Inventory.objects.filter(internal_part_number=master).count(), 1)