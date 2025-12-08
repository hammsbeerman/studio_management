from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from inventory.models import InventoryMaster, InventoryRetailPrice
from controls.models import RetailInventoryCategory


DEFAULT_RETAIL_MARKUP_PERCENT = Decimal("50.00")  # 50% default if nothing set
DEFAULT_RETAIL_MARKUP_FLAT = Decimal("0.00")


def _calc_price_from_cost(
    cost: Decimal,
    percent: Optional[Decimal],
    flat: Optional[Decimal],
) -> Decimal:
    """
    Helper to compute a retail price from cost + percent + flat.

    - percent is a % (e.g. 50.00 = 50%)
    - flat is a dollar add-on
    """
    cost = cost or Decimal("0.00")

    pct = Decimal("0.00")
    if percent is not None:
        try:
            pct = Decimal(percent)
        except Exception:
            pct = Decimal("0.00")

    flat_add = Decimal("0.00")
    if flat is not None:
        try:
            flat_add = Decimal(flat)
        except Exception:
            flat_add = Decimal("0.00")

    factor = Decimal("1.00") + (pct / Decimal("100.00"))
    raw = (cost * factor) + flat_add

    # Always round to 2 decimals, like POS
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_retail_price(item: InventoryMaster) -> Decimal:
    """
    Single source of truth for POS retail pricing.

    Priority:
      1) item.retail_price if set
      2) item.retail_markup_percent / retail_markup_flat
      3) category.default_markup_percent / default_markup_flat
      4) global defaults
    """
    cost = item.unit_cost or Decimal("0.00")

    # 1) Hard-set retail price on the item wins over everything
    if item.retail_price is not None:
        try:
            return Decimal(item.retail_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            # fall back to computed if somehow invalid
            pass

    # 2) Item-specific markup (percent and/or flat)
    if item.retail_markup_percent is not None or item.retail_markup_flat is not None:
        return _calc_price_from_cost(cost, item.retail_markup_percent, item.retail_markup_flat)

    # 3) Category defaults
    cat: RetailInventoryCategory | None = getattr(item, "retail_category", None)
    if cat and (cat.default_markup_percent is not None or cat.default_markup_flat is not None):
        return _calc_price_from_cost(cost, cat.default_markup_percent, cat.default_markup_flat)

    # 4) Global defaults
    return _calc_price_from_cost(cost, DEFAULT_RETAIL_MARKUP_PERCENT, DEFAULT_RETAIL_MARKUP_FLAT)

def ensure_retail_pricing(item: InventoryMaster, reset_override: bool = False) -> InventoryRetailPrice:
    """
    Ensure there is an InventoryRetailPrice row for this item and refresh
    purchase_price + calculated_price from current cost/markup.

    If reset_override=True, override_price is cleared (used when new inventory is received).
    """
    cost = item.unit_cost or Decimal("0.00")
    calc_price = compute_retail_price(item)

    # Get or create WITHOUT touching override unless explicitly asked.
    rp, created = InventoryRetailPrice.objects.get_or_create(
        inventory=item,
    )

    rp.purchase_price = cost
    rp.calculated_price = calc_price

    if reset_override:
        rp.override_price = None

    rp.save()
    return rp


def get_effective_retail_price(item: InventoryMaster) -> Decimal:
    """
    Price POS should use as default when adding a line.

    Priority:
    1) override_price
    2) calculated_price
    3) purchase_price
    4) freshly computed price as last fallback
    """
    try:
        # IMPORTANT: fetch fresh from DB, don't use item.retail_pricing cache
        rp = InventoryRetailPrice.objects.get(inventory=item)
    except InventoryRetailPrice.DoesNotExist:
        rp = ensure_retail_pricing(item)

    if rp.override_price is not None:
        return rp.override_price
    if rp.calculated_price is not None:
        return rp.calculated_price
    if rp.purchase_price is not None:
        return rp.purchase_price

    return compute_retail_price(item)