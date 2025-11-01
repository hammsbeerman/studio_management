from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from controls.models import (
    Category, SubCategory, SetPriceCategory, SetPriceItemPrice,
    GroupCategory, Measurement
)
from inventory.models import (
    InventoryMaster, InventoryPricingGroup, InventoryQtyVariations
)

User = get_user_model()

class ControlsViewsTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Standard", setprice=True)
        self.url_add_subcategory = reverse("controls:add_subcategory")
        self.user = User.objects.create_user("admin", password="pw123456")
        self.client.force_login(self.user)

        # common URLs (adjust names if your project differs)
        self.url_add_category = reverse("controls:add_category")
        self.url_add_subcategory = reverse("controls:add_subcategory")
        self.url_add_sp_cat = reverse("controls:add_setprice_category")
        self.url_add_sp_item = reverse("controls:add_setprice_item")
        self.url_view_groups = reverse("controls:view_price_groups")
        self.url_add_group = reverse("controls:add_price_group")
        self.url_add_item_variation = reverse("controls:add_item_variation")
        self.url_add_base_qty_variation = reverse("controls:add_base_qty_variation")
        self.url_add_primary_baseunit = reverse("controls:add_primary_baseunit")
        self.url_add_units_per_base_unit = reverse("controls:add_units_per_base_unit")

    def test_add_category_creates_and_triggers(self):
        url = reverse("controls:add_category")
        resp = self.client.post(url, {"name": "Stickers"})
        self.assertEqual(resp.status_code, 204)
        self.assertIn("HX-Trigger", resp.headers)
        self.assertTrue(Category.objects.filter(name="Stickers").exists())

    def test_add_subcategory_setprice_creates_setpricecategory(self):
        url = reverse("controls:add_subcategory")
        resp = self.client.post(url, {
            "category": self.cat.id,
            "name": "Standard",
            "description": "Desc",
        })
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(SubCategory.objects.filter(name="Standard", set_price=True).exists())
        self.assertTrue(SetPriceCategory.objects.filter(category=self.cat, name="Standard").exists())

    def test_missing_workorders_no_eval(self):
        url = reverse("controls:missing_workorders")
        resp = self.client.post(url, {"start": "1", "end": "10", "company": "1"})
        self.assertEqual(resp.status_code, 200)  # page renders safely

    def test_add_category_get(self):
        resp = self.client.get(self.url_add_category)
        self.assertEqual(resp.status_code, 200)

    def test_add_category_post_creates_category_and_sends_hx(self):
        resp = self.client.post(self.url_add_category, data={"name": "Cards"})
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.headers.get("HX-Trigger"), "CategoryListChanged")
        self.assertTrue(Category.objects.filter(name="Cards").exists())

    def test_add_subcategory_post_setprice_false(self):
        cat = Category.objects.create(name="General", setprice=False)
        resp = self.client.post(self.url_add_subcategory, data={
            "category": cat.id, "name": "SubA",
        })
        self.assertEqual(resp.status_code, 204)
        sub = SubCategory.objects.get(name="SubA")
        self.assertFalse(sub.set_price)
        self.assertFalse(SetPriceCategory.objects.filter(name="SubA").exists())

    def test_add_subcategory_post_setprice_true(self):
        cat = Category.objects.create(name="SP", setprice=True)
        resp = self.client.post(self.url_add_subcategory, data={
            "category": cat.id, "name": "SP Sub",
        })
        self.assertEqual(resp.status_code, 204)
        sub = SubCategory.objects.get(name="SP Sub")
        self.assertTrue(sub.set_price)
        self.assertTrue(SetPriceCategory.objects.filter(name="SP Sub", category=cat).exists())

    def test_add_setprice_category_post(self):
        cat = Category.objects.create(name="ForSP")
        resp = self.client.post(self.url_add_sp_cat, data={
            "name": "Menus",
            "category": cat.id,
        })
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(SetPriceCategory.objects.filter(name="Menus", category=cat).exists())

    def test_add_setprice_item_post(self):
        cat = Category.objects.create(name="C")
        sp = SetPriceCategory.objects.create(name="Rack Cards", category=cat, created=timezone.now())
        resp = self.client.post(self.url_add_sp_item, data={
            "name": sp.id,  # FK field name is 'name' on the model
            "description": "500 qty",
            "set_quantity": "500",
            "price": "99.99",
        })
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.headers.get("HX-Trigger"), "TemplateListChanged")
        self.assertTrue(SetPriceItemPrice.objects.filter(name=sp, description="500 qty").exists())

    # ----- Price Groups -----

    def test_view_price_groups_get(self):
        GroupCategory.objects.create(name="Banners")
        resp = self.client.get(self.url_view_groups)
        self.assertEqual(resp.status_code, 200)

    def test_add_price_group_post_creates_group(self):
        resp = self.client.post(self.url_add_group, data={"group_name": "Yard Signs"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(GroupCategory.objects.filter(name="Yard Signs").exists())

    def test_view_price_group_detail_lists_items(self):
        g = GroupCategory.objects.create(name="Labels")
        item = InventoryMaster.objects.create(name="1\" Circle")
        InventoryPricingGroup.objects.create(inventory=item, group=g)
        url = reverse("controls:view_price_group_detail", kwargs={"id": g.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_add_price_group_item_assigns_items(self):
        g = GroupCategory.objects.create(name="Stickers")
        item = InventoryMaster.objects.create(name="BOPP 4x6")
        url = reverse("controls:add_price_group_item", kwargs={"id": g.id})
        resp = self.client.post(url, data={"group_id": g.id, "item": [str(item.id)]})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(InventoryPricingGroup.objects.filter(inventory=item, group=g).exists())
        item.refresh_from_db()
        self.assertTrue(item.grouped)

    def test_add_price_group_item_flags_notgrouped(self):
        g = GroupCategory.objects.create(name="Decals")
        item = InventoryMaster.objects.create(name="Cast Vinyl")
        url = reverse("controls:add_price_group_item", kwargs={"id": g.id})
        resp = self.client.post(url, data={"notgrouped": "1", "group_id": g.id, "item": [str(item.id)]})
        self.assertEqual(resp.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.not_grouped)

    # ----- Inventory helpers -----

    def test_add_item_variation_get(self):
        resp = self.client.get(self.url_add_item_variation)
        self.assertEqual(resp.status_code, 200)

    def test_add_primary_baseunit_creates_variation(self):
        unit = Measurement.objects.create(name="Each")
        item = InventoryMaster.objects.create(name="Aluminum Panel")
        resp = self.client.post(self.url_add_primary_baseunit, data={
            "unit": unit.id,
            "qty": "10",
            "item": [str(item.id)],
        })
        self.assertEqual(resp.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.units_per_base_unit, 10)
        self.assertEqual(item.primary_base_unit_id, unit.id)
        self.assertTrue(InventoryQtyVariations.objects.filter(inventory=item, variation=unit, variation_qty=10).exists())

    def test_add_units_per_base_unit_updates_items(self):
        item = InventoryMaster.objects.create(name="Foamcore 3/16")
        resp = self.client.post(self.url_add_units_per_base_unit, data={
            "qty": "25",
            "item": [str(item.id)],
        })
        self.assertEqual(resp.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.units_per_base_unit, 25)

    def test_add_base_qty_variation_adds_missing_variations(self):
        unit = Measurement.objects.create(name="Box")
        item = InventoryMaster.objects.create(name="Envelopes A7", primary_base_unit=unit, units_per_base_unit=250)
        # ensure no variation exists yet
        self.assertFalse(InventoryQtyVariations.objects.filter(inventory=item).exists())
        resp = self.client.get(self.url_add_base_qty_variation)
        self.assertEqual(resp.status_code, 302)  # redirects to controls:utilities
        self.assertTrue(InventoryQtyVariations.objects.filter(inventory=item, variation=unit, variation_qty=250).exists())