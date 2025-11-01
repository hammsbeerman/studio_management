from decimal import Decimal

from django.db.utils import IntegrityError
from django.test import TestCase

from controls.models import (
    Numbering,
    FixedCost,
    InventoryCategory,
    GroupCategory,
    Category,
    SubCategory,
    SetPriceCategory,
    SetPriceItemPrice,
    DesignType,
    Measurement,
    JobStatus,
    UserGroup,
    PaymentType,
    RetailInventoryCategory,
    RetailInventorySubCategory,
)


class NumberingTests(TestCase):
    def test_unique_name_and_str(self):
        n = Numbering.objects.create(name="WorkorderCounter", value=100)
        self.assertEqual(str(n), "WorkorderCounter")
        with self.assertRaises(IntegrityError):
            Numbering.objects.create(name="WorkorderCounter", value=101)


class SimpleNameStrTests(TestCase):
    def test_str_returns_name(self):
        pairs = [
            (InventoryCategory, {"name": "Paper"}),
            (GroupCategory, {"name": "Wide Format Vinyl"}),
            (DesignType, {"name": "Logo", "description": "Logo design"}),
            (Measurement, {"name": "Each"}),
            (JobStatus, {"name": "In Progress"}),
            (UserGroup, {"name": "Production"}),
            (PaymentType, {"name": "Credit Card"}),
            (RetailInventoryCategory, {"name": "Shirts"}),
            (RetailInventorySubCategory, {"name": "Short Sleeve"}),
        ]
        for model, kwargs in pairs:
            obj = model.objects.create(**kwargs)
            self.assertEqual(str(obj), kwargs["name"])


class CategoryTreeTests(TestCase):
    def test_category_and_subcategory(self):
        cat = Category.objects.create(name="Business Cards", description="Std business cards")
        self.assertEqual(str(cat), "Business Cards")
        sub = SubCategory.objects.create(category=cat, name="14pt", description="14pt gloss")
        self.assertEqual(str(sub), "14pt")
        # FK linkage is correct
        self.assertEqual(sub.category, cat)


class FixedCostTests(TestCase):
    def test_create_with_some_nulls(self):
        f = FixedCost.objects.create(name="Default Costs", create_workorder=Decimal("5.00"))
        self.assertEqual(str(f), "Default Costs")
        self.assertEqual(f.create_workorder, Decimal("5.00"))
        # Optional fields can be null
        self.assertIsNone(f.reclaim_artwork)


class SetPriceTests(TestCase):
    def test_setprice_category_and_item_price(self):
        cat = Category.objects.create(name="Flyers")
        spc = SetPriceCategory.objects.create(category=cat, name="100 Pack")
        self.assertEqual(str(spc), "100 Pack")

        item = SetPriceItemPrice.objects.create(
            name=spc,
            description="100 flyers",
            set_quantity=Decimal("100"),
            price=Decimal("29.99"),
        )
        self.assertEqual(str(item), "100 flyers")
        self.assertEqual(item.set_quantity, Decimal("100"))
        self.assertEqual(item.price, Decimal("29.99"))


class RetailRelationsTests(TestCase):
    def test_subcategory_m2m_links(self):
        parent = RetailInventoryCategory.objects.create(name="Apparel")
        sub = RetailInventorySubCategory.objects.create(name="Hoodies")
        sub.inventory_category.add(parent)
        self.assertEqual(sub.inventory_category.count(), 1)
        self.assertEqual(sub.inventory_category.first(), parent)