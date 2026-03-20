from decimal import Decimal
from django.test import TestCase

from controls.models import Measurement
from inventory.models import InventoryMaster, InventoryQtyVariations
from inventory.services.uom_rows import get_or_create_uom_row


class GetOrCreateUomRowTests(TestCase):
    def setUp(self):
        self.measurement = Measurement.objects.create(name="Each")
        self.item = InventoryMaster.objects.create(
            name="Test Item",
            non_inventory=False,
        )

    def test_reactivates_exact_inactive_match(self):
        row = InventoryQtyVariations.objects.create(
            inventory=self.item,
            variation=self.measurement,
            variation_qty=Decimal("1.0000"),
            active=False,
        )

        found = get_or_create_uom_row(
            item=self.item,
            measurement=self.measurement,
            qty=Decimal("1.0000"),
        )

        self.assertEqual(found.id, row.id)
        found.refresh_from_db()
        self.assertTrue(found.active)

    def test_reuses_existing_exact_active_match(self):
        row = InventoryQtyVariations.objects.create(
            inventory=self.item,
            variation=self.measurement,
            variation_qty=Decimal("1.0000"),
            active=True,
        )

        found = get_or_create_uom_row(
            item=self.item,
            measurement=self.measurement,
            qty=Decimal("1.0000"),
        )

        self.assertEqual(found.id, row.id)
        self.assertEqual(
            InventoryQtyVariations.objects.filter(
                inventory=self.item,
                variation=self.measurement,
                variation_qty=Decimal("1.0000"),
            ).count(),
            1,
        )