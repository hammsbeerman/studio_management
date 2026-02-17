from decimal import Decimal, InvalidOperation

def as_decimal(val, default="0"):
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)

def variation_multiplier(variation) -> Decimal:
    """
    variation: InventoryQtyVariations or None
    Returns multiplier to convert 'variation units' -> base units.
    """
    if not variation:
        return Decimal("1")
    mult = getattr(variation, "variation_qty", None)
    return as_decimal(mult, default="1") or Decimal("1")

def qty_to_base(qty, variation=None) -> Decimal:
    """
    qty: entered quantity in the chosen unit (variation or base)
    variation: InventoryQtyVariations or None
    """
    q = as_decimal(qty, default="0")
    if q == 0:
        return Decimal("0")
    return q * variation_multiplier(variation)