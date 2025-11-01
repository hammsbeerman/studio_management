from django.db import IntegrityError, transaction
from django.test import TestCase

from inventory.models import InventoryMaster, Vendor, VendorItemDetail

class VendorItemDetailUniqueTests(TestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(name="V1")
        self.ipn = InventoryMaster.objects.create(name="Paper A")

    def test_unique_vendor_per_ipn(self):
        VendorItemDetail.objects.create(
            vendor=self.vendor,
            internal_part_number=self.ipn,
            name="Row1",
            supplies=True, retail=True, non_inventory=False, online_store=False,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VendorItemDetail.objects.create(
                    vendor=self.vendor,
                    internal_part_number=self.ipn,
                    name="Dup",
                    supplies=True, retail=True, non_inventory=False, online_store=False,
                )