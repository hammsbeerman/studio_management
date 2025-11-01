import pytest
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from inventory.models import OrderOut, Vendor
from customers.models import Customer

class OrderOutConstraintTests(TestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(name="Test Vendor")
        self.customer = Customer.objects.create(company_name="Test Customer")

    def test_open_and_billed_cannot_both_be_true(self):
        oo = OrderOut(
            vendor=self.vendor,
            customer=self.customer,
            open=True,
            billed=True,  # violates oo_not_both_open_and_billed
            description="Bad flags",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                oo.save()

    # @pytest.mark.parametrize(
    #     "field,value",
    #     [
    #         ("purchase_price", Decimal("-0.01")),
    #         ("percent_markup", Decimal("-1")),
    #         ("quantity", Decimal("-1")),
    #         ("unit_price", Decimal("-0.0001")),
    #         ("total_price", Decimal("-0.01")),
    #     ],
    # )
    # def test_non_negative_numeric_fields(self, field, value):
    #     kwargs = dict(
    #         vendor=self.vendor,
    #         customer=self.customer,
    #         open=False,
    #         billed=False,
    #         description="neg test",
    #     )
    #     kwargs[field] = value
    #     oo = OrderOut(**kwargs)
    #     with self.assertRaises(IntegrityError):
    #         with transaction.atomic():
    #             oo.save()

    def test_non_negative_numeric_fields(self):
        cases = [
            ("purchase_price", Decimal("-0.01")),
            ("percent_markup", Decimal("-1")),
            ("quantity", Decimal("-1")),
            ("unit_price", Decimal("-0.0001")),
            ("total_price", Decimal("-0.01")),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                oo = OrderOut(vendor=self.vendor, customer=self.customer, description="x")
                setattr(oo, field, value)
                with self.assertRaises(ValidationError):
                    oo.full_clean()