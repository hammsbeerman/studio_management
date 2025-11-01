import factory
from factory import Faker, LazyAttribute, Sequence
from factory.django import DjangoModelFactory

# Import your models
from inventory.models import InventoryMaster, InventoryPricingGroup, Vendor, Measurement
from controls.models import GroupCategory
# If WorkorderItem lives in another app, adjust this import:
from workorders.models import WorkorderItem


class VendorFactory(DjangoModelFactory):
    class Meta:
        model = Vendor

    name = Sequence(lambda n: f"Vendor {n}")


class MeasurementFactory(DjangoModelFactory):
    class Meta:
        model = Measurement

    name = Sequence(lambda n: f"Unit {n}")
    abbreviation = LazyAttribute(lambda o: o.name[:3].upper() if hasattr(o, "name") else "UNT")


class GroupCategoryFactory(DjangoModelFactory):
    class Meta:
        model = GroupCategory

    name = Sequence(lambda n: f"GroupCategory {n}")


class InventoryMasterFactory(DjangoModelFactory):
    class Meta:
        model = InventoryMaster

    name = Sequence(lambda n: f"Item {n}")
    internal_part_number = Sequence(lambda n: f"IPN-{n:05d}")
    is_active = True
    primary_vendor = factory.SubFactory(VendorFactory)
    primary_vendor_part_number = Faker("bothify", text="PVPN-####")
    primary_base_unit = factory.SubFactory(MeasurementFactory)
    units_per_base_unit = 1
    supplies = True
    retail = True
    non_inventory = False
    online_store = True
    not_grouped = False
    grouped = False
    unit_cost = 1.25
    price_per_m = 10.00
    high_price = 12.50


class InventoryPricingGroupFactory(DjangoModelFactory):
    class Meta:
        model = InventoryPricingGroup

    inventory = factory.SubFactory(InventoryMasterFactory)
    group = factory.SubFactory(GroupCategoryFactory)
    high_price = None


class WorkorderItemFactory(DjangoModelFactory):
    class Meta:
        model = WorkorderItem

    inventory_item = factory.SubFactory(InventoryMasterFactory)
    qty = 1