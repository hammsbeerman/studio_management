from django.test import TestCase
from inventory.models import Vendor

class SmokeTests(TestCase):
    def test_can_create_vendor(self):
        v = Vendor.objects.create(name="Acme")
        self.assertEqual(v.name, "Acme")