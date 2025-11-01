import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="pass1234"
    )

@pytest.mark.django_db
@pytest.mark.parametrize("urlname", [
    "admin:inventory_inventorymaster_changelist",
    "admin:inventory_inventory_changelist",
    "admin:inventory_inventorypricinggroup_changelist",
    "admin:inventory_orderout_changelist",
])
def test_admin_pages_load(client, superuser, urlname):
    client.login(username="admin", password="pass1234")
    resp = client.get(reverse(urlname))
    assert resp.status_code == 200