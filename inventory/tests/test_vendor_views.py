from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from inventory.models import Vendor
from django.urls import reverse

PATH_VENDOR_LIST = reverse("inventory:vendor_list")
PATH_VENDOR_LIST_KIND = "/inventory/vendors/{kind}/"  # OK to format, or use reverse with kwargs
PATH_VENDOR_ADD = reverse("inventory:add_vendor")
def PATH_VENDOR_DETAIL_ID(id): return reverse("inventory:vendor_detail", kwargs={"id": id})
def PATH_VENDOR_EDIT_ID(id): return reverse("inventory:edit_vendor", kwargs={"id": id})


class VendorViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(self.user)
        # build a little matrix of vendors for filtering tests
        self.v_all = Vendor.objects.create(name="AllCo")  # defaults make it show in 'All'
        self.v_retail = Vendor.objects.create(
            name="RetailCo", retail_vendor=True, supplier=False, inventory_vendor=False, non_inventory_vendor=False
        )
        self.v_supply = Vendor.objects.create(
            name="SupplyCo", retail_vendor=False, supplier=True, inventory_vendor=False, non_inventory_vendor=False
        )
        self.v_inventory = Vendor.objects.create(
            name="InventoryCo", retail_vendor=False, supplier=False, inventory_vendor=True, non_inventory_vendor=False
        )
        self.v_noninv = Vendor.objects.create(
            name="NonInvCo", retail_vendor=False, supplier=False, inventory_vendor=False, non_inventory_vendor=True
        )
        self.v_other = Vendor.objects.create(
            name="OtherCo", retail_vendor=False, supplier=False, inventory_vendor=False, non_inventory_vendor=False
        )

    def test_vendor_list_base(self):
        resp = self.client.get(PATH_VENDOR_LIST)
        self.assertEqual(resp.status_code, 200)
        # Should use the full list template
        self.assertTemplateUsed(resp, "inventory/vendors/list.html")
        self.assertContains(resp, "AllCo")
        self.assertContains(resp, "RetailCo")

    def test_vendor_list_filter_retail(self):
        resp = self.client.get(PATH_VENDOR_LIST_KIND.format(kind="Retail"))
        self.assertEqual(resp.status_code, 200)
        # Filtered lists use the partial template per your CBV
        self.assertTemplateUsed(resp, "inventory/vendors/partials/vendor_list.html")
        self.assertContains(resp, "RetailCo")
        self.assertNotContains(resp, "SupplyCo")
        self.assertNotContains(resp, "OtherCo")

    def test_vendor_list_filter_supply(self):
        resp = self.client.get(PATH_VENDOR_LIST_KIND.format(kind="Supply"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "SupplyCo")
        self.assertNotContains(resp, "RetailCo")

    def test_vendor_list_filter_inventory(self):
        resp = self.client.get(PATH_VENDOR_LIST_KIND.format(kind="Inventory"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "InventoryCo")
        self.assertNotContains(resp, "RetailCo")

    def test_vendor_list_filter_noninventory(self):
        resp = self.client.get(PATH_VENDOR_LIST_KIND.format(kind="NonInventory"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "NonInvCo")
        self.assertNotContains(resp, "RetailCo")

    def test_vendor_list_filter_other(self):
        resp = self.client.get(PATH_VENDOR_LIST_KIND.format(kind="Other"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "OtherCo")
        self.assertNotContains(resp, "RetailCo")

    def test_vendor_detail_basic(self):
        resp = self.client.get(PATH_VENDOR_DETAIL_ID(self.v_retail.id))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/vendors/detail.html")
        self.assertContains(resp, "RetailCo")  # name appears on the page

    def test_add_vendor_get(self):
        resp = self.client.get(PATH_VENDOR_ADD)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/vendors/add_vendor.html")

    def test_add_vendor_get_htmx_modal(self):
        # Simulate HTMX request to hit the modal branch
        resp = self.client.get(
            PATH_VENDOR_ADD,
            HTTP_HX_REQUEST="true",
            data={"item": "123", "cat": "Whatever"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "inventory/vendors/add_vendor_modal.html")

    def test_add_vendor_post(self):
        count_before = Vendor.objects.count()
        resp = self.client.post(PATH_VENDOR_ADD, data={"name": "NewCo"})
        self.assertEqual(resp.status_code, 200)  # your view renders the list on success
        self.assertEqual(Vendor.objects.count(), count_before + 1)
        self.assertTrue(Vendor.objects.filter(name="NewCo").exists())

    def test_edit_vendor_post(self):
        v = Vendor.objects.create(name="EditMe")
        resp = self.client.post(PATH_VENDOR_EDIT_ID(v.id), data={"name": "EditedCo"})
        self.assertEqual(resp.status_code, 200)  # your view renders the list on success
        v.refresh_from_db()
        self.assertEqual(v.name, "EditedCo")