# inventory/tests/test_item_forms.py
from django.test import TestCase
from inventory.models import InventoryMaster, Inventory
from controls.forms import AddItemtoListForm  # same import your view uses

class ItemFormTests(TestCase):
    def setUp(self):
        # Create a master; Inventory row should be created by the post_save signal
        self.master = InventoryMaster.objects.create(name="FormTarget")
        self.inv = Inventory.objects.get(internal_part_number=self.master)

    def test_add_item_to_list_form_instantiates_with_instance(self):
        form = AddItemtoListForm(instance=self.inv)
        # Unbound form => not valid; this just ensures it constructs without exploding.
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.fields)  # has fields

    def test_add_item_to_list_form_rejects_empty_post(self):
        form = AddItemtoListForm(data={}, instance=self.inv)
        self.assertFalse(form.is_valid())