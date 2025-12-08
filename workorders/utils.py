from decimal import Decimal
from workorders.models import WorkorderItem

def apply_pos_adjustment_to_workorder(workorder, amount, tax_amount=Decimal("0.00")):
    """
    Create or update a single 'POS Adjustment' item on this workorder
    so its total reflects POS refunds/credits.

    `amount` will be NEGATIVE for a refund.
    """
    adj_item, created = WorkorderItem.objects.get_or_create(
        workorder=workorder,
        description="Retail POS Adjustment",
        defaults={
            "billable": True,
            "absolute_price": amount,
            "tax_amount": tax_amount,
            "total_with_tax": amount + tax_amount,
        },
    )
    if not created:
        adj_item.absolute_price = (adj_item.absolute_price or 0) + amount
        adj_item.tax_amount = (adj_item.tax_amount or 0) + tax_amount
        adj_item.total_with_tax = (adj_item.total_with_tax or 0) + amount + tax_amount
        adj_item.save(
            update_fields=["absolute_price", "tax_amount", "total_with_tax"]
        )