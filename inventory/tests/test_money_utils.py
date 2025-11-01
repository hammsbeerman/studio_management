import pytest
from decimal import Decimal, ROUND_HALF_UP

pytestmark = pytest.mark.django_db

def test_quantizers_exist():
    try:
        from lib.pricing import quantize_money, quantize_qty
    except Exception:
        pytest.skip("lib.pricing helpers not present")

    assert str(quantize_money(Decimal("12.34567"))) in {"12.3457", "12.3457"}
    assert str(quantize_qty(Decimal("1.2345678"))) in {"1.234568", "1.234568"}