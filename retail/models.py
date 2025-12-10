from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from customers.models import Customer
from inventory.models import InventoryMaster, InventoryQtyVariations
from workorders.models import Workorder


class RetailSale(models.Model):
    STATUS_OPEN = "open"
    STATUS_ON_HOLD = "hold"
    STATUS_COMPLETED = "completed"
    STATUS_VOID = "void"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_ON_HOLD, "On Hold"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_VOID, "Void"),
    ]

    INTERNAL_COMPANY_CHOICES = [
        ("LK Design", "LK Design"),
        ("Krueger Printing", "Krueger Printing"),
        ("Office Supplies", "Office Supplies"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="retail_sales")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="retail_sales")
    customer_name = models.CharField(max_length=255, blank=True)
    internal_company = models.CharField(max_length=100, choices=INTERNAL_COMPANY_CHOICES, default="Office Supplies")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    notes = models.TextField(blank=True, null=True)
    workorder = models.ForeignKey(Workorder, on_delete=models.SET_NULL, null=True, blank=True, related_name="retail_sales")
    tax_exempt = models.BooleanField("Tax Exempt", default=False, help_text="If true, no tax will be charged on this sale.")
    tax_rate = models.DecimalField("Tax Rate", max_digits=5, decimal_places=3, default=Decimal("0.055"), help_text="Tax rate as a decimal (e.g. 0.055 for 5.5%).")
    locked = models.BooleanField(default=False, help_text="When true, POS lines and customer should not be edited.")
    paid_at = models.DateTimeField(null=True, blank=True, help_text="When this sale was fully paid (POS).")
    is_refund = models.BooleanField(default=False)
    original_sale = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds", help_text="If set, this sale is a refund/adjustment of the original sale.")
    requires_delivery = models.BooleanField(default=False, help_text="If true, this sale should be included on the delivery list.")

    @property
    def subtotal(self):
        return sum(line.extended for line in self.lines.all())

    @property
    def tax_total(self):
        return sum(line.tax_amount for line in self.lines.all())

    @property
    def total(self):
        return self.subtotal + self.tax_total

    @property
    def paid_amount(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance_due(self):
        return self.total - self.paid_amount

    @property
    def is_paid(self):
        return self.status == self.STATUS_COMPLETED

    @property
    def is_locked(self):
        return bool(self.locked)


class RetailSaleLine(models.Model):
    sale = models.ForeignKey(RetailSale, on_delete=models.CASCADE, related_name="lines")
    inventory = models.ForeignKey(InventoryMaster, on_delete=models.PROTECT, related_name="retail_lines", null=True, blank=True)
    description = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sold_variation = models.ForeignKey(InventoryQtyVariations, on_delete=models.SET_NULL, null=True, blank=True, related_name="retail_sale_lines", help_text="If set, qty represents this variation; base units = qty * sold_variation.variation_qty.")

    @property
    def extended(self):
        return (self.qty or Decimal("0")) * (self.unit_price or Decimal("0"))

    @property
    def tax_amount(self):
        rate = (self.tax_rate or Decimal("0")) / Decimal("100")
        return self.extended * rate

    def get_line_total(self):
        qty = self.qty or Decimal("0")
        price = self.unit_price or Decimal("0")
        return qty * price


class RetailPayment(models.Model):
    TYPE_CASH = "cash"
    TYPE_CARD = "card"
    TYPE_CHECK = "check"
    TYPE_OTHER = "other"

    PAYMENT_TYPES = [
        (TYPE_CASH, "Cash"),
        (TYPE_CARD, "Card"),
        (TYPE_CHECK, "Check"),
        (TYPE_OTHER, "Other"),
    ]

    sale = models.ForeignKey(RetailSale, on_delete=models.CASCADE, related_name="payments")
    created_at = models.DateTimeField(auto_now_add=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True)


class RetailCashSale(models.Model):
    sale = models.OneToOneField("retail.RetailSale", on_delete=models.CASCADE, related_name="cash_record")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, help_text="Usually the Walk-in / Cash Sale customer record.")
    created_at = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, default="Cash")
    payment_notes = models.CharField(max_length=200, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    def __str__(self):
        return f"Cash sale #{self.pk} for POS sale #{self.sale_id}"
    
class DeliveryRouteEntry(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="delivery_route_entry")
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["sort_order", "customer__company_name"]

    def __str__(self):
        return f"Route order {self.sort_order} for {self.customer}"


class Delivery(models.Model):
    STATUS_PENDING = "pending"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    sale = models.OneToOneField("retail.RetailSale", on_delete=models.CASCADE, related_name="delivery")
    workorder = models.OneToOneField("workorders.Workorder", on_delete=models.CASCADE, related_name="delivery", null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="deliveries")
    scheduled_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Delivery for sale #{self.sale_id} to {self.customer}"