from decimal import Decimal

from django.test import TestCase

from inventory.models import InventoryMaster, Inventory, InventoryLedger
from inventory.services.ledger import record_inventory_movement, get_on_hand


class InventoryLedgerOnHandTests(TestCase):
    def setUp(self):
        InventoryLedger.objects.all().delete()
        Inventory.objects.all().delete()
        InventoryMaster.objects.all().delete()

    def test_sale_and_refund_adjust_on_hand_via_ledger(self):
        """
        Basic flow:

        - Start with 0 on hand
        - AP_RECEIPT +10  → on_hand = 10
        - POS_SALE -3     → on_hand = 7
        - POS_REFUND +1   → on_hand = 8
        """
        item = InventoryMaster.objects.create(
            name="Test Item",
            non_inventory=False,
        )

        self.assertEqual(get_on_hand(item), Decimal("0"))

        # Stock in: +10
        record_inventory_movement(
            inventory_item=item,
            qty_delta=Decimal("10.0000"),
            source_type="AP_RECEIPT",
            source_id="test-ap-1",
            note="Initial receipt",
        )
        self.assertEqual(get_on_hand(item), Decimal("10.0000"))

        # POS sale: -3
        record_inventory_movement(
            inventory_item=item,
            qty_delta=Decimal("-3.0000"),
            source_type="POS_SALE",
            source_id="pos-1",
            note="Sold 3 units",
        )
        self.assertEqual(get_on_hand(item), Decimal("7.0000"))

        # POS refund: +1
        record_inventory_movement(
            inventory_item=item,
            qty_delta=Decimal("1.0000"),
            source_type="POS_REFUND",
            source_id="refund-1",
            note="Refund 1 unit",
        )
        self.assertEqual(get_on_hand(item), Decimal("8.0000"))

    def test_legacy_inventory_current_stock_fallback_then_ledger_takes_over(self):
        """
        - When there are no ledger rows, get_on_hand falls back to Inventory.current_stock.
        - Once ledger rows exist and sum != 0, ledger total wins.
        """
        item = InventoryMaster.objects.create(
            name="Legacy Item",
            non_inventory=False,
        )

        Inventory.objects.create(
            name="Legacy row",
            internal_part_number=item,
            current_stock="5",
        )

        # No ledger: uses legacy current_stock
        self.assertEqual(get_on_hand(item), Decimal("5"))

        # Now ledger entry: +2
        record_inventory_movement(
            inventory_item=item,
            qty_delta=Decimal("2.0000"),
            source_type="ADJUSTMENT",
            source_id="adj-1",
            note="Manual adjustment",
        )

        # Ledger total 2 (non-zero) → overrides fallback
        self.assertEqual(get_on_hand(item), Decimal("2.0000"))