from django.test import TestCase
from inventory.models import InventoryMaster, InventoryQtyVariations
from controls.models import Measurement

class InventoryQtyVariationsTests(TestCase):
    def setUp(self):
        self.mea = Measurement.objects.create(name="Each")
        self.inv1 = InventoryMaster.objects.create(name="Item 1")
        self.inv2 = InventoryMaster.objects.create(name="Item 2")
        InventoryQtyVariations.objects.create(inventory=self.inv1, variation=self.mea, variation_qty=1)
        InventoryQtyVariations.objects.create(inventory=self.inv1, variation=self.mea, variation_qty=2)
        InventoryQtyVariations.objects.create(inventory=self.inv2, variation=self.mea, variation_qty=3)

    def test_distinct_inventories(self):
        rows = InventoryQtyVariations.objects.distinct_inventories()
        # should return one row per inventory (order: inv1 first occurrence, then inv2)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.inventory_id for r in rows}, {self.inv1.id, self.inv2.id})