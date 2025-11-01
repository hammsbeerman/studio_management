import pytest
from django.utils import timezone
from decimal import Decimal

from controls.models import GroupCategory, Measurement
from customers.models import Customer
from inventory.models import Vendor, InventoryMaster, Inventory, InventoryPricingGroup, OrderOut

@pytest.fixture
def vendor(db):
    return Vendor.objects.create(name="Acme Supplies")

@pytest.fixture
def measurement(db):
    return Measurement.objects.create(name="Each")

@pytest.fixture
def group(db):
    return GroupCategory.objects.create(name="Paper / Stock")

@pytest.fixture
def customer(db):
    return Customer.objects.create(company_name="Umbrella Corp")

@pytest.fixture
def master(db, vendor, measurement):
    return InventoryMaster.objects.create(
        name="80# Text White",
        description="House stock",
        primary_vendor=vendor,
        primary_base_unit=measurement,
        units_per_base_unit=Decimal("1.0"),
        unit_cost=Decimal("12.3400"),
        price_per_m=Decimal("150.0000"),
        retail=True,
        supplies=True,
        non_inventory=False,
        online_store=True,
    )

@pytest.fixture
def inv_variant(db, master, measurement):
    return Inventory.objects.create(
        name="80# Text White 12x18",
        internal_part_number=master,
        measurement=measurement,
        unit_cost=Decimal("12.3400"),
        price_per_m=Decimal("150.0000"),
        retail_item=True,
    )

@pytest.fixture
def user_factory(django_user_model):
    def _make_user(**kwargs):
        defaults = dict(username="tester", email="tester@example.com")
        defaults.update(kwargs)
        return django_user_model.objects.create_user(
            password=kwargs.pop("password", "pass1234"),
            **defaults
        )
    return _make_user