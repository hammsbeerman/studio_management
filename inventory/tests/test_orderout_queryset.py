import pytest
from django.utils import timezone
from datetime import timedelta
from inventory.models import OrderOut, Vendor
from customers.models import Customer

@pytest.mark.django_db
def test_recent_queryset_filters_by_days(vendor, cust):
    # create 3 orders, then move 1 of them back 40 days
    o1 = OrderOut.objects.create(customer=cust, vendor=vendor, description="nowish", open=True)
    o2 = OrderOut.objects.create(customer=cust, vendor=vendor, description="nowish2", open=True)
    old = OrderOut.objects.create(customer=cust, vendor=vendor, description="old", open=True)

    forty_days_ago = timezone.now() - timedelta(days=40)
    OrderOut.objects.filter(pk=old.pk).update(dateentered=forty_days_ago)

    recent = OrderOut.objects.recent(days=30)
    ids = list(recent.values_list("id", flat=True))
    assert o1.id in ids and o2.id in ids
    assert old.id not in ids

@pytest.fixture
def vendor(db):
    return Vendor.objects.create(name="Acme")

@pytest.fixture
def cust(db):
    return Customer.objects.create(company_name="Initech")