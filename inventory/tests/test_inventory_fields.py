import pytest
from decimal import Decimal

@pytest.mark.django_db
def test_inventory_variant_pricing_fallback(master, inv_variant):
    # variant has explicit pricing → use it
    assert inv_variant.unit_cost == Decimal("12.3400")
    # remove variant pricing → should still have master-level attrs available via properties (if you use them)
    inv_variant.unit_cost = None
    inv_variant.price_per_m = None
    inv_variant.save()
    # if you kept the `*_effective` helpers:
    assert inv_variant.unit_cost_effective == master.unit_cost
    assert inv_variant.price_per_m_effective == master.price_per_m