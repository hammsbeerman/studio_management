# inventory/tests/test_item_views.py
from decimal import Decimal
from django.test import TestCase
from inventory.models import InventoryMaster, InventoryQtyVariations, Inventory
# If you have named URLs, feel free to swap these paths for reverse(...) calls.
PATH_ITEM_VARIATIONS           = "/inventory/items/variations/"
PATH_ITEM_VARIATION_DETAILS_ID = "/inventory/items/variations/{id}/"
PATH_ITEM_DETAILS              = "/inventory/items/details/"
PATH_ITEM_DETAILS_ID           = "/inventory/items/details/{id}/"


class ItemViewsTests(TestCase):
    def setUp(self):
        # Two masters, each with at least one variation row
        self.inv1 = InventoryMaster.objects.create(name="Item 1")
        self.inv2 = InventoryMaster.objects.create(name="Item 2")

        InventoryQtyVariations.objects.create(
            inventory=self.inv1, variation=None, variation_qty=Decimal("1.0")
        )
        InventoryQtyVariations.objects.create(
            inventory=self.inv2, variation=None, variation_qty=Decimal("2.0")
        )

        # Ensure the Inventory (child) exists for item_details (created by your signal)
        self.child1 = Inventory.objects.get(internal_part_number=self.inv1)
        self.child2 = Inventory.objects.get(internal_part_number=self.inv2)

    # -----------------------
    # /inventory/items/variations/
    # -----------------------
    def test_item_variations_lists_unique_masters(self):
        resp = self.client.get(PATH_ITEM_VARIATIONS)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/items/view_variations.html")
        # The context should contain the unique_list with inv1 and inv2
        unique_list = list(resp.context["unique_list"])
        ids = {obj.id for obj in unique_list}
        self.assertSetEqual(ids, {self.inv1.id, self.inv2.id})

    # -----------------------
    # /inventory/items/variations/<id>/
    # -----------------------
    def test_item_variation_details_filters_by_inventory(self):
        # add an extra variation for inv1 so we can check filtering count
        InventoryQtyVariations.objects.create(
            inventory=self.inv1, variation=None, variation_qty=Decimal("3.0")
        )
        resp = self.client.get(PATH_ITEM_VARIATION_DETAILS_ID.format(id=self.inv1.id))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/items/view_variation_details.html")
        variations = list(resp.context["variations"])
        self.assertTrue(all(v.inventory_id == self.inv1.id for v in variations))
        self.assertEqual(len(variations), 2)

    # -----------------------
    # /inventory/items/details/ (no id)
    # -----------------------
    def test_item_details_without_id_renders_base_template(self):
        resp = self.client.get(PATH_ITEM_DETAILS)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/items/item_details.html")
        # Should include the list of masters in context
        items = list(resp.context["items"])
        self.assertGreaterEqual(len(items), 2)

    # -----------------------
    # /inventory/items/details/<id>/
    # -----------------------
    def test_item_details_with_id_renders_partial_template(self):
        resp = self.client.get(PATH_ITEM_DETAILS_ID.format(id=self.inv1.id))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/items/partials/item_details.html")
        # Should include master + form + item (purchase_history) in context
        self.assertEqual(resp.context["master"].id, self.inv1.id)
        self.assertIn("form", resp.context)
        self.assertIn("item", resp.context)

    # -----------------------
    # /inventory/items/details/?name=<id> (query param path)
    # -----------------------
    def test_item_details_with_query_param_name_renders_partial_template(self):
        resp = self.client.get(PATH_ITEM_DETAILS, {"name": self.inv2.id})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/items/partials/item_details.html")
        self.assertEqual(resp.context["master"].id, self.inv2.id)

    # -----------------------
    # POST invalid -> partial template (no crash)
    # -----------------------
    def test_item_details_post_invalid_renders_partial(self):
        # Empty POST likely invalid for your AddItemtoListForm; view should render partial anyway.
        resp = self.client.post(PATH_ITEM_DETAILS_ID.format(id=self.inv1.id), data={})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/items/partials/item_details.html")
        self.assertIn("form", resp.context)