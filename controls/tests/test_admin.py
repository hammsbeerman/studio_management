from django.contrib import admin
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


class AdminRegistrationTests(TestCase):
    def test_models_are_registered(self):
        for model in [
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
        ]:
            with self.subTest(model=model.__name__):
                self.assertIn(model, admin.site._registry)