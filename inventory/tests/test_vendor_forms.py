from django.test import TestCase
from inventory.forms import AddVendorForm

class AddVendorFormTests(TestCase):
    def test_valid_with_minimal_fields(self):
        form = AddVendorForm(data={"name": "FormCo"})
        self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_invalid_without_name(self):
        form = AddVendorForm(data={"name": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)