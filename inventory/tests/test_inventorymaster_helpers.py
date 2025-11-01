from django.test import TestCase
from controls.models import Measurement
from inventory.models import InventoryMaster, InventoryQtyVariations


class InventoryMasterHelperTests(TestCase):
    def test_set_primary_base_unit_creates_variation_and_sets_qty(self):
        unit = Measurement.objects.create(name="Pack")
        item = InventoryMaster.objects.create(name="Business Cards")
        # method under test (ensure this exists in your model)
        item.set_primary_base_unit(unit, qty=100)

        item.refresh_from_db()
        self.assertEqual(item.primary_base_unit_id, unit.id)
        self.assertEqual(item.units_per_base_unit, 100)
        self.assertTrue(
            InventoryQtyVariations.objects.filter(
                inventory=item, variation=unit, variation_qty=100
            ).exists()
        )

    def test_ensure_base_variation_idempotent(self):
        unit = Measurement.objects.create(name="Sheet")
        item = InventoryMaster.objects.create(
            name="Labels",
            primary_base_unit=unit,
            units_per_base_unit=50,
        )
        # first call creates it
        item.ensure_base_variation()
        self.assertEqual(InventoryQtyVariations.objects.filter(inventory=item).count(), 1)
        # second call keeps it at one (no dupes)
        item.ensure_base_variation()
        self.assertEqual(InventoryQtyVariations.objects.filter(inventory=item).count(), 1)