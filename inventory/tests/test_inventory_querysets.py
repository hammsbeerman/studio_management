from django.test import TestCase
from django.utils import timezone
from inventory.models import Vendor, OrderOut
from customers.models import Customer
from workorders.models import Workorder

class VendorQuerySetTests(TestCase):
    def setUp(self):
        Vendor.objects.create(name="Alpha", supplier=True, retail_vendor=False, inventory_vendor=False, non_inventory_vendor=False)
        Vendor.objects.create(name="Bravo", supplier=False, retail_vendor=True, inventory_vendor=False, non_inventory_vendor=False)
        Vendor.objects.create(name="Charlie", supplier=False, retail_vendor=False, inventory_vendor=True, non_inventory_vendor=False)
        Vendor.objects.create(name="Delta", supplier=False, retail_vendor=False, inventory_vendor=False, non_inventory_vendor=True)
        Vendor.objects.create(name="Echo", supplier=False, retail_vendor=False, inventory_vendor=False, non_inventory_vendor=False)

    def test_by_kind_all_orders_by_name(self):
        names = list(Vendor.objects.by_kind("All").values_list("name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_by_kind_retail(self):
        qs = Vendor.objects.by_kind("Retail")
        self.assertEqual(qs.count(), 1)
        self.assertTrue(qs.first().retail_vendor)

    def test_by_kind_supply(self):
        qs = Vendor.objects.by_kind("Supply")
        self.assertEqual(qs.count(), 1)
        self.assertTrue(qs.first().supplier)

    def test_by_kind_inventory(self):
        qs = Vendor.objects.by_kind("Inventory")
        self.assertEqual(qs.count(), 1)
        self.assertTrue(qs.first().inventory_vendor)

    def test_by_kind_noninventory(self):
        qs = Vendor.objects.by_kind("NonInventory")
        self.assertEqual(qs.count(), 1)
        self.assertTrue(qs.first().non_inventory_vendor)

    def test_by_kind_other(self):
        qs = Vendor.objects.by_kind("Other")
        self.assertEqual(qs.count(), 1)
        self.assertFalse(qs.first().supplier or qs.first().retail_vendor or qs.first().inventory_vendor or qs.first().non_inventory_vendor)


class OrderOutQuerySetTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(company_name="TestCo")
        self.workorder = Workorder.objects.create(
            customer=self.customer,
            workorder="WO-1",
            internal_company="LK Design",
            quote="0",
            notes="",
        )
        self.v1 = Vendor.objects.create(name="Vendor A")
        self.v2 = Vendor.objects.create(name="Vendor B")

        self.o1 = OrderOut.objects.create(workorder=self.workorder, vendor=self.v1, billed=False)
        self.o2 = OrderOut.objects.create(workorder=self.workorder, vendor=self.v1, billed=True)
        self.o3 = OrderOut.objects.create(workorder=self.workorder, vendor=self.v2, billed=False)

    def test_for_vendor_accepts_instance(self):
        qs = OrderOut.objects.for_vendor(self.v1)
        self.assertQuerySetEqual(qs.order_by("id"), [self.o1, self.o2], transform=lambda x: x)

    def test_for_vendor_accepts_id(self):
        qs = OrderOut.objects.for_vendor(self.v2.id)
        self.assertQuerySetEqual(qs.order_by("id"), [self.o3], transform=lambda x: x)

    def test_open_and_billed(self):
        self.assertQuerySetEqual(OrderOut.objects.open().order_by("id"), [self.o1, self.o3], transform=lambda x: x)
        self.assertQuerySetEqual(OrderOut.objects.billed().order_by("id"), [self.o2], transform=lambda x: x)

    def test_recent(self):
        # Everything is auto_now_add "now", so recent(30) should include all
        self.assertEqual(OrderOut.objects.recent(30).count(), 3)