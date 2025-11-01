from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from django.apps import apps
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.db.models import Min, Max, Q, OuterRef, Subquery
from django.urls import reverse
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError

from customers.models import Customer
from workorders.models import Workorder
from controls.models import Measurement, InventoryCategory, GroupCategory

from studio_management.lib.pricing import (
    compute_unit_cost,
    compute_price_per_m,
    quantize_money,
    quantize_cost,
    quantize_per_m,
)

def quantize_rate_m(value, places="0.01"):
    return Decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)

if TYPE_CHECKING:
    from inventory.models import Vendor

User = get_user_model()

# -----------------------------
# QuerySets / Managers
# -----------------------------
class VendorQuerySet(models.QuerySet):
    def ordered(self): return self.order_by("name")
    def retail(self): return self.filter(retail_vendor=True)
    def supply(self): return self.filter(supplier=True)
    def inventory_vendors(self): return self.filter(inventory_vendor=True)
    def non_inventory(self): return self.filter(non_inventory_vendor=True)
    def other(self):
        return self.filter(
            supplier=False,
            retail_vendor=False,
            inventory_vendor=False,
            non_inventory_vendor=False,
        )
    def by_kind(self, kind: str):
        k = (kind or "").strip().lower()
        qs = self
        if k == "retail": qs = qs.filter(retail_vendor=True)
        elif k == "supply": qs = qs.filter(supplier=True)
        elif k == "inventory": qs = qs.filter(inventory_vendor=True)
        elif k == "noninventory": qs = qs.filter(non_inventory_vendor=True)
        elif k == "other": qs = qs.filter(
            retail_vendor=False,
            supplier=False,
            inventory_vendor=False,
            non_inventory_vendor=False,
        )
        return qs.order_by("name")
    
class InventoryManager(models.Manager):
    def _alias_kwargs(self, kwargs):
        if 'internal_part_number' in kwargs:
            kwargs = dict(kwargs)
            kwargs['master'] = kwargs.pop('internal_part_number')
        return kwargs


class OrderOutQuerySet(models.QuerySet):
    def for_vendor(self, vendor_or_id):
        vid = getattr(vendor_or_id, "id", vendor_or_id)
        return self.filter(vendor_id=vid)
    def for_customer(self, customer_or_id):
        cid = getattr(customer_or_id, "id", customer_or_id)
        return self.filter(customer_id=cid)
    def billed(self):
        names = {f.name for f in self.model._meta.get_fields()}
        q = models.Q()
        if "billed" in names: q |= models.Q(billed=True)
        if "is_billed" in names: q |= models.Q(is_billed=True)
        if "billed_at" in names: q |= models.Q(billed_at__isnull=False)
        if "status" in names: q |= models.Q(status__in=["BILLED", "INVOICED"])
        return self.filter(q) if q.children else self.none()
    def open(self):
        return self.exclude(pk__in=self.billed().values_list("pk", flat=True))
    def recent(self, days: Optional[int] = 30):
        qs = self.order_by("-dateentered")
        if days is not None:
            cutoff = timezone.now() - timedelta(days=days)
            qs = qs.filter(dateentered__gte=cutoff)
        return qs


class InventoryMasterQuerySet(models.QuerySet):
    def eager(self):
        return self.select_related("primary_vendor", "primary_base_unit") \
                   .prefetch_related("price_group")
    def with_highest_invoice_cost(self):
        InvoiceItem = apps.get_model("finance", "InvoiceItem")
        max_cost_subq = (
            InvoiceItem.objects
            .filter(internal_part_number=OuterRef("pk"))
            .values("internal_part_number")
            .annotate(m=Max("unit_cost"))
            .values("m")[:1]
        )
        return self.annotate(highest_invoice_cost=Subquery(max_cost_subq))


InventoryMasterManager = models.Manager.from_queryset(InventoryMasterQuerySet)

# -----------------------------
# Models
# -----------------------------
class Vendor(models.Model):
    name = models.CharField('Name', max_length=200)
    address1 = models.CharField('Address 1', max_length=100, blank=True, null=True)
    address2 = models.CharField('Address 2', max_length=100, blank=True, null=True)
    city = models.CharField('City', max_length=100, blank=True, null=True)
    state = models.CharField('State', max_length=100, blank=True, null=True)
    zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=True)
    phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=True)
    phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=True)
    email = models.EmailField('Email', max_length=100, blank=True, null=True)
    website = models.URLField('Website', max_length=100, blank=True, null=True)
    supplier = models.BooleanField('Supplier', default=True)
    retail_vendor = models.BooleanField('Retail Vendor', default=True)
    inventory_vendor = models.BooleanField('Inventory Vendor', default=True)
    online_store_vendor = models.BooleanField('Online Store Vendor', default=False)
    non_inventory_vendor = models.BooleanField('Non Inventory Vendor', default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    void = models.BooleanField(default=False)
    objects = VendorQuerySet.as_manager()
    class Meta: ordering = ("name",)
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse("inventory:vendor_detail", kwargs={"id": self.id})


from decimal import Decimal
from django.apps import apps
from django.db.models import Q
# ... other imports

class InventoryMaster(models.Model):
    name = models.CharField('Name', max_length=200)
    internal_part_number = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True)
    merged_into = models.ForeignKey('self', null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='merged_children')
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    primary_vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL)
    primary_vendor_part_number = models.CharField('Primary Vendor Part Number', max_length=100, blank=True, null=True)
    primary_base_unit = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
    units_per_base_unit = models.DecimalField('Units per base unit', max_digits=15, decimal_places=6, blank=True, null=True)

    # ⬇️ tests expect 6dp on the *master* object
    unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=6, blank=True, null=True)
    price_per_m = models.DecimalField('Price Per M', max_digits=15, decimal_places=6, blank=True, null=True)

    supplies = models.BooleanField('Supply Item', default=True)
    retail = models.BooleanField('Retail Item', default=True)
    non_inventory = models.BooleanField('Non Inventory Item', default=False)
    online_store = models.BooleanField('Online Store Item', default=True)
    not_grouped = models.BooleanField('Not Price Grouped', default=False)
    grouped = models.BooleanField('In price group', default=False)

    price_group = models.ManyToManyField(
        'controls.GroupCategory',
        through='inventory.InventoryPricingGroup',
        through_fields=('inventory', 'group'),
        related_name='items',
        blank=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    high_price = models.DecimalField('High Price', max_digits=15, decimal_places=6, blank=True, null=True)

    objects = InventoryMasterManager()

    def __str__(self):
        return self.name

    def purchase_history(self):
        # FK filter by instance is fine; keep order_by on invoice date
        InvoiceItem = apps.get_model("finance", "InvoiceItem")
        return (InvoiceItem.objects
                .filter(internal_part_number=self)
                .select_related("invoice", "vendor")
                .order_by("-invoice__invoice_date"))

    def add_to_group(self, group):
        """
        Accepts GroupCategory instance or id.
        Creates through row only if missing and flips grouped/not_grouped flags.
        """
        InventoryPricingGroup = apps.get_model('inventory', 'InventoryPricingGroup')
        group_id = getattr(group, "id", group)
        # ⬇️ critical fix: use the real FK name on the through model
        InventoryPricingGroup.objects.get_or_create(group_id=group_id, inventory=self)
        self.grouped = True
        self.not_grouped = False
        self.save(update_fields=["grouped", "not_grouped", "updated"])

    def add_to_price_group(self, group):
        # Backwards-compatible shim to old name used by tests.
        return self.add_to_group(group)

    def set_primary_base_unit(self, unit, qty: int):
        unit_id = unit.id if hasattr(unit, "id") else int(unit)
        self.primary_base_unit_id = unit_id
        self.units_per_base_unit = qty
        self.save(update_fields=["primary_base_unit", "units_per_base_unit", "updated"])
        self.ensure_base_variation()

    def set_units_per_base_unit(self, qty: int):
        self.units_per_base_unit = qty
        self.save(update_fields=["units_per_base_unit", "updated"])
        self.ensure_base_variation()

    def ensure_base_variation(self):
        """
        Ensure a 1× base qty-variation row exists for this inventory.
        Do NOT depend on a Variation model; the base row uses variation=None.
        """
        from .models import InventoryQtyVariations
        if not self.primary_base_unit_id or not self.units_per_base_unit:
            return
        InventoryQtyVariations.objects.update_or_create(
            inventory=self,
            variation_id=self.primary_base_unit_id,  # variation FK points to Measurement
            defaults={"variation_qty": self.units_per_base_unit},
        )

    class Meta:
        constraints = [
            # Allow NULL or > 0 (so creating an item without qty doesn’t violate)
            models.CheckConstraint(
                check=Q(units_per_base_unit__isnull=True) | Q(units_per_base_unit__gt=0),
                name="ipn_units_per_base_unit_gt_0_or_null",
            ),
        ]




# class InventoryMaster(models.Model):
#     name = models.CharField('Name', max_length=200)
#     internal_part_number = models.CharField(max_length=64, blank=True, null=True, db_index=True)
#     is_active = models.BooleanField(default=True)
#     merged_into = models.ForeignKey('self', null=True, blank=True,
#                                     on_delete=models.SET_NULL, related_name='merged_children')
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     primary_vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL)
#     primary_vendor_part_number = models.CharField('Primary Vendor Part Number', max_length=100, blank=True, null=True)
#     primary_base_unit = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
#     units_per_base_unit = models.DecimalField('Units per base unit', max_digits=15, decimal_places=6, blank=True, null=True)
#     unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
#     price_per_m = models.DecimalField('Price Per M', max_digits=15, decimal_places=4, blank=True, null=True)
#     supplies = models.BooleanField('Supply Item', default=True)
#     retail = models.BooleanField('Retail Item', default=True)
#     non_inventory = models.BooleanField('Non Inventory Item', default=False)
#     online_store = models.BooleanField('Online Store Item', default=True)
#     not_grouped = models.BooleanField('Not Price Grouped', default=False)
#     grouped = models.BooleanField('In price group', default=False)
#     price_group = models.ManyToManyField(
#         'controls.GroupCategory',
#         through='inventory.InventoryPricingGroup',
#         through_fields=('inventory', 'group'),
#         related_name='items',
#         blank=True,
#     )
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
#     high_price = models.DecimalField('High Price', max_digits=15, decimal_places=6, blank=True, null=True)
#     objects = InventoryMasterManager()
#     def __str__(self): return self.name
#     def purchase_history(self):
#         InvoiceItem = apps.get_model("finance", "InvoiceItem")
#         return (InvoiceItem.objects.filter(internal_part_number=self.pk)
#                 .select_related("invoice", "vendor")
#                 .order_by("-invoice__invoice_date"))
    
#     def add_to_group(self, group):
#     # """
#     # Accepts GroupCategory instance or id.
#     # Creates through row only if missing and flips grouped/not_grouped flags.
#     # """
#         from controls.models import GroupCategory  # adjust if your through model differs
#         from inventory.models import InventoryPricingGroup
#         group_id = getattr(group, "id", group)
#         GroupCategory.objects.filter(pk=group_id).exists()  # sanity; let DoesNotExist bubble if needed
#         # through table name in your project may be different; use your actual through model:
#         InventoryPricingGroup.objects.get_or_create(group_id=group_id, internal_part_number=self)
#         self.grouped = True
#         self.not_grouped = False
#         self.save(update_fields=["grouped", "not_grouped", "updated"])

#     def add_to_price_group(self, group):
#         # """
#         # Backwards-compatible shim to old name used by tests.
#         # """
#         return self.add_to_group(group)

#     def set_primary_base_unit(self, unit, qty: int):
#         # """
#         # Sets primary_base_unit and units_per_base_unit.
#         # Also ensures base variation exists.
#         # """
#         from controls.models import Measurement
#         unit_id = unit.id if hasattr(unit, "id") else int(unit)
#         self.primary_base_unit_id = unit_id
#         self.units_per_base_unit = qty
#         self.save(update_fields=["primary_base_unit", "units_per_base_unit", "updated"])
#         self.ensure_base_variation()

#     def set_units_per_base_unit(self, qty: int):
#         self.units_per_base_unit = qty
#         self.save(update_fields=["units_per_base_unit", "updated"])
#         self.ensure_base_variation()

#     # def ensure_base_variation(self):
#     #     # """
#     #     # Ensure InventoryQtyVariations has a base row for this item & base unit.
#     #     # """
#     #     if not self.primary_base_unit_id or not self.units_per_base_unit:
#     #         return
#     #     InventoryQtyVariations.objects.get_or_create(
#     #         master=self,
#     #         unit_id=self.primary_base_unit_id,
#     #         defaults={"qty": self.units_per_base_unit},
#     #     )

#     def ensure_base_variation(self):
#         from inventory.models import InventoryQtyVariations, Variation  # adjust if variation model named differently
#         # Create a 1x base variation if missing
#         InventoryQtyVariations.objects.get_or_create(
#             inventory=self,
#             variation=None,     # or your base Variation object if required
#             defaults={'variation_qty': 1}
#         )

#     class Meta:
#         constraints = [
#             models.CheckConstraint(
#                 check=Q(units_per_base_unit__gt=0),
#                 name="ipn_units_per_base_unit_gt_0",
#             ),
#         ]


class Inventory(models.Model):
    internal_part_number = models.ForeignKey('InventoryMaster', on_delete=models.CASCADE, related_name='inventories', null=True, blank=True, db_index=True)
    name = models.CharField('Name', max_length=100)
    name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, null=True, blank=True)
    price_per_m = models.DecimalField('Price Per M', max_digits=15, decimal_places=4, null=True, blank=True)
    price_per_sqft = models.CharField('Price per SqFt', max_length=100, blank=True, null=True)
    current_stock = models.CharField('Current Stock', max_length=100, blank=True, null=True)
    color = models.CharField('Color', max_length=100, blank=True, null=True)
    size = models.CharField('Size', max_length=100, blank=True, null=True)
    width = models.CharField('Width', max_length=100, blank=True, null=True)
    width_measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='width_mea')
    length = models.CharField('Length', max_length=100, blank=True, null=True)
    length_measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='length_mea')
    measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING)
    type_paper = models.BooleanField('Paper', default=False)
    type_envelope = models.BooleanField('Envelope', default=False)
    type_wideformat = models.BooleanField('Wide Format', default=False)
    type_vinyl = models.BooleanField('Vinyl', default=False)
    type_mask = models.BooleanField('Mask', default=False)
    type_laminate = models.BooleanField('Laminate', default=False)
    type_substrate = models.BooleanField('Substrate', default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    inventory_category = models.ManyToManyField(InventoryCategory)
    retail_item = models.BooleanField('Retail Item', default=True)

    objects = InventoryManager()


    def purchase_history(self):
        """Mirror the master’s purchase history if linked; else empty."""
        if self.internal_part_number_id:
            return self.internal_part_number.purchase_history()
        InvoiceItem = apps.get_model("finance", "InvoiceItem")
        return InvoiceItem.objects.none()
    

    # read-only property so templates/old code can still access it
    # @property
    # def internal_part_number(self):
    #     return self.internal_part_number

    @property
    def unit_cost_effective(self):
        return self.unit_cost if self.unit_cost is not None else getattr(self.internal_part_number, "unit_cost", None)

    @property
    def price_per_m_effective(self):
        return self.price_per_m if self.price_per_m is not None else getattr(self.internal_part_number, "price_per_m", None)


    def __str__(self): return self.name or f"Inventory #{self.pk}"


class VendorItemDetail(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100)
    vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="vendor_details")
    supplies = models.BooleanField('Supply Item')
    retail = models.BooleanField('Retail Item')
    non_inventory = models.BooleanField('Non Inventory Item')
    online_store = models.BooleanField('Online Store Item')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    high_price = models.DecimalField('High Price', max_digits=15, decimal_places=4, blank=True, null=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["internal_part_number", "vendor"],
                name="uq_vendor_detail_once_per_vendor",
            )
        ]
    def __str__(self):
        vend = self.vendor.name if self.vendor else "Unknown vendor"
        return f"{vend} → {self.internal_part_number.name}"


class InventoryPricingGroup(models.Model):
    inventory = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="pricing_group_links")
    group = models.ForeignKey(GroupCategory, on_delete=models.CASCADE, related_name="item_links")
    high_price = models.DecimalField('High Price', max_digits=15, decimal_places=4, blank=True, null=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['inventory', 'group'], name='uniq_inventory_group_once')
        ]
        indexes = [
            models.Index(fields=['inventory']),
            models.Index(fields=['group']),
        ]
    def __str__(self): return f"{self.inventory} ↔ {self.group}"
    def get_absolute_url(self): return reverse("controls:view_price_group_detail", kwargs={"id": self.group.id})

class InventoryQtyVariationsManager(models.Manager):
    def distinct_inventories(self):
        qs = self.get_queryset()
        first_ids = (
            qs.values("inventory_id")
              .annotate(first_id=Min("id"))
              .values_list("first_id", flat=True)
        )
        return qs.filter(id__in=list(first_ids)).order_by("inventory_id", "id")

class InventoryQtyVariations(models.Model):
    inventory = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
    variation = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
    variation_qty = models.DecimalField('Variation Qty', max_digits=15, decimal_places=4)

    objects = InventoryQtyVariationsManager()

    class Meta:
        indexes = [
            models.Index(fields=['inventory']),
            models.Index(fields=['variation']),
        ]

    def __str__(self):
        return f"{self.inventory.name} — {self.variation} = {self.variation_qty}"

    def get_absolute_url(self):
        return reverse("inventory:item_variation_details", kwargs={"id": self.inventory.id})


class InternalCompany(models.TextChoices):
    LK = "LK Design", "LK Design"
    KRUEGER = "Krueger Printing", "Krueger Printing"
    OFFICE = "Office Supplies", "Office Supplies"


class OrderOut(models.Model):
    workorder = models.ForeignKey(Workorder, blank=False, null=True, on_delete=models.CASCADE)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField('Internal Company', max_length=32, choices=InternalCompany.choices)
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    vendor = models.ForeignKey('Vendor', blank=True, null=True, on_delete=models.SET_NULL)
    purchase_price = models.DecimalField('Purchase Price', max_digits=8, decimal_places=2, blank=True, null=True)
    percent_markup = models.DecimalField('Percent Markup', max_digits=8, decimal_places=2, blank=True, null=True)
    quantity = models.DecimalField('Quantity', max_digits=8, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    dateentered = models.DateTimeField(auto_now_add=True)
    open = models.BooleanField(default=False, db_index=True)
    billed = models.BooleanField('Billed', default=False, db_index=True)
    edited = models.BooleanField('Edited', default=False)
    objects = OrderOutQuerySet.as_manager()
    def clean(self):
        if self.open and self.billed:
            raise ValidationError("OrderOut cannot be both open and billed.")
    class Meta:
        ordering = ["-dateentered"]
        indexes = [models.Index(fields=["billed"]), models.Index(fields=["dateentered"]), models.Index(fields=["vendor", "dateentered"])]
        constraints = [
        models.CheckConstraint(
            check=~(Q(open=True) & Q(billed=True)),
            name="oo_not_both_open_and_billed",
        ),
        models.CheckConstraint(
            check=(Q(purchase_price__gte=0) | Q(purchase_price__isnull=True)),
            name="oo_purchase_price_nonneg",
        ),
        models.CheckConstraint(
            check=(Q(percent_markup__gte=0) | Q(percent_markup__isnull=True)),
            name="oo_percent_markup_nonneg",
        ),
        models.CheckConstraint(
            check=(Q(quantity__gte=0) | Q(quantity__isnull=True)),
            name="oo_quantity_nonneg",
        ),
        models.CheckConstraint(
            check=(Q(unit_price__gte=0) | Q(unit_price__isnull=True)),
            name="oo_unit_price_nonneg",
        ),
        models.CheckConstraint(
            check=(Q(total_price__gte=0) | Q(total_price__isnull=True)),
            name="oo_total_price_nonneg",
        ),
    ]
    def __str__(self): return f"OrderOut #{self.pk} to {(self.vendor.name if self.vendor else 'Unknown Vendor')}"

class SetPrice(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField(
        'Internal Company',
        choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')],
        max_length=100,
    )
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    setprice_category = models.CharField('Item Category', max_length=10, blank=True, null=True)
    setprice_item = models.CharField('Item', max_length=10, blank=True, null=True)
    setprice_qty = models.CharField('Pieces / set', max_length=10, blank=True, null=True)
    setprice_price = models.CharField('Price / set', max_length=10, blank=True, null=True)
    total_pieces = models.CharField('Total pieces', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    paper_stock = models.ForeignKey('Inventory', blank=True, null=True, on_delete=models.SET_NULL)
    side_1_inktype = models.CharField(
        'Side 1 Ink',
        choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')],
        max_length=100, blank=True, null=True
    )
    side_2_inktype = models.CharField(
        'Side 2 Ink',
        choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')],
        max_length=100, blank=True, null=True
    )
    quantity = models.PositiveIntegerField('Quantity', blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    dateentered = models.DateTimeField(auto_now_add=True)
    billed = models.BooleanField('Billed', default=False)
    edited = models.BooleanField('Edited', default=False)

    def __str__(self):
        return self.workorder.workorder

class Photography(models.Model):
    workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
    hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
    workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
    internal_company = models.CharField(
        'Internal Company',
        choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')],
        max_length=100,
    )
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
    category = models.CharField('Category', max_length=10, blank=True, null=True)
    subcategory = models.CharField('Subcategory', max_length=10, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    quantity = models.DecimalField('Quantity', max_digits=6, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    dateentered = models.DateTimeField(auto_now_add=True)
    billed = models.BooleanField('Billed', default=False)
    edited = models.BooleanField('Edited', default=False)


# -----------------------------
# Signal to sync pricing
# -----------------------------
def _str6(d: Optional[Decimal]) -> str:
    if d is None: return ""
    return f"{d:.6f}"

@receiver(post_save, sender=InventoryMaster)
def recompute_and_sync_pricing(sender, instance: InventoryMaster, created, **kwargs):
    def _do():
        unit_cost_dec: Optional[Decimal] = None
        per_m_dec: Optional[Decimal] = None
        if instance.high_price and instance.units_per_base_unit:
            unit_cost_dec = quantize_money(Decimal(instance.high_price) / Decimal(instance.units_per_base_unit))
            per_m_dec = quantize_rate_m(unit_cost_dec * Decimal("1000"))
            InventoryMaster.objects.filter(pk=instance.pk).update(
                unit_cost=unit_cost_dec, price_per_m=per_m_dec, updated=timezone.now()
            )
        inv, _created = Inventory.objects.get_or_create(
            internal_part_number=instance,
            defaults={
                "name": instance.name,
                "description": instance.description or "",
                "unit_cost": unit_cost_dec,
                "price_per_m": per_m_dec,
                "retail_item": instance.retail,
            },
        )
        updates = {}
        if inv.name != instance.name: updates["name"] = instance.name
        if (inv.description or "") != (instance.description or ""): updates["description"] = instance.description or ""
        if inv.retail_item != instance.retail: updates["retail_item"] = instance.retail
        if unit_cost_dec is not None and inv.unit_cost != unit_cost_dec: updates["unit_cost"] = unit_cost_dec
        if per_m_dec is not None and inv.price_per_m != per_m_dec: updates["price_per_m"] = per_m_dec
        if updates:
            updates["updated"] = timezone.now()
            Inventory.objects.filter(pk=inv.pk).update(**updates)
    transaction.on_commit(_do)


# from __future__ import annotations

# from typing import Optional, TYPE_CHECKING
# from datetime import timedelta
# from decimal import Decimal, ROUND_HALF_UP

# from django.utils import timezone
# from django.apps import apps
# from django.db import models, transaction
# from django.contrib.auth import get_user_model
# from django.db.models import Min, Max, Q, F, OuterRef, Subquery, CheckConstraint
# from django.urls import reverse
# from django.shortcuts import get_object_or_404
# from django.dispatch import receiver
# from django.db.models.signals import post_save
# from django.core.exceptions import ValidationError

# from customers.models import Customer
# from workorders.models import Workorder
# from controls.models import Measurement, InventoryCategory, GroupCategory

# from studio_management.lib.pricing import (
#     compute_unit_cost,
#     compute_price_per_m,
#     quantize_money,
#     quantize_cost,
#     quantize_per_m,
# )

# def quantize_rate_m(value, places="0.01"):
#     return Decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)

# if TYPE_CHECKING:
#     # Only imported for typing; not at runtime
#     from controls.models import GroupCategory, Measurement
#     from inventory.models import Vendor

# User = get_user_model()
# # -----------------------------
# # QuerySets / Managers
# # -----------------------------
# class VendorQuerySet(models.QuerySet):
#     def ordered(self):
#         return self.order_by("name")

#     def retail(self):
#         return self.filter(retail_vendor=True)

#     def supply(self):
#         return self.filter(supplier=True)

#     def inventory_vendors(self):
#         return self.filter(inventory_vendor=True)

#     def non_inventory(self):
#         return self.filter(non_inventory_vendor=True)

#     def other(self):
#         return self.filter(
#             supplier=False,
#             retail_vendor=False,
#             inventory_vendor=False,
#             non_inventory_vendor=False,
#         )

#     def by_kind(self, kind: str):
#         """
#         Filter vendors by a human-readable 'kind' label.
#         Kinds (case-insensitive): All, Retail, Supply, Inventory, NonInventory, Other.
#         Always ordered by name.
#         """
#         k = (kind or "").strip().lower()
#         qs = self
#         if k == "retail":
#             qs = qs.filter(retail_vendor=True)
#         elif k == "supply":
#             qs = qs.filter(supplier=True)
#         elif k == "inventory":
#             qs = qs.filter(inventory_vendor=True)
#         elif k == "noninventory":
#             qs = qs.filter(non_inventory_vendor=True)
#         elif k == "other":
#             qs = qs.filter(
#                 retail_vendor=False,
#                 supplier=False,
#                 inventory_vendor=False,
#                 non_inventory_vendor=False,
#             )
#         # else: "all" or unknown -> no extra filter
#         return qs.order_by("name")
    
# # class InventoryItem(models.Model):
# #     name = models.CharField(max_length=200)
# #     sku = models.CharField(max_length=64, blank=True, null=True, db_index=True)
# #     is_active = models.BooleanField(default=True)
# #     merged_into = models.ForeignKey("self", null=True, blank=True,
# #                                     on_delete=models.SET_NULL, related_name="merged_children")
# #     # … your existing fields …

# #     def __str__(self):
# #         return f"{self.name} ({self.pk})"


# class OrderOutQuerySet(models.QuerySet):
#     def for_vendor(self, vendor_or_id):
#         vid = getattr(vendor_or_id, "id", vendor_or_id)
#         return self.filter(vendor_id=vid)

#     def for_customer(self, customer_or_id):
#         cid = getattr(customer_or_id, "id", customer_or_id)
#         return self.filter(customer_id=cid)

#     def billed(self):
#         """
#         Billed if:
#         - billed / is_billed boolean is True, or
#         - billed_at is not null, or
#         - status in BILLED/INVOICED
#         """
#         names = {f.name for f in self.model._meta.get_fields()}
#         q = models.Q()
#         if "billed" in names:
#             q |= models.Q(billed=True)
#         if "is_billed" in names:
#             q |= models.Q(is_billed=True)
#         if "billed_at" in names:
#             q |= models.Q(billed_at__isnull=False)
#         if "status" in names:
#             q |= models.Q(status__in=["BILLED", "INVOICED"])

#         return self.filter(q) if q.children else self.none()

#     def open(self):
#         """
#         OPEN = not billed. We deliberately ignore any 'open/closed' flags.
#         """
#         # Option A (subquery): simple and clear
#         return self.exclude(pk__in=self.billed().values_list("pk", flat=True))

#         # Option B (no subquery): uncomment if you prefer building the negated Q directly.
#         # names = {f.name for f in self.model._meta.get_fields()}
#         # q = models.Q()
#         # if "billed" in names:
#         #     q |= models.Q(billed=True)
#         # if "is_billed" in names:
#         #     q |= models.Q(is_billed=True)
#         # if "billed_at" in names:
#         #     q |= models.Q(billed_at__isnull=False)
#         # if "status" in names:
#         #     q |= models.Q(status__in=["BILLED", "INVOICED"])
#         # return self.exclude(q) if q.children else self

#     def recent(self, days: Optional[int] = 30):
#         qs = self.order_by("-dateentered")
#         if days is not None:
#             cutoff = timezone.now() - timedelta(days=days)
#             qs = qs.filter(dateentered__gte=cutoff)
#         return qs

# class InventoryMasterQuerySet(models.QuerySet):
#     def eager(self):
#         """Select/prefetch relations commonly used in views & admin."""
#         return self.select_related("primary_vendor", "primary_base_unit")\
#                    .prefetch_related("price_group")

#     def with_highest_invoice_cost(self):
#         """Annotate each item with its highest invoice unit_cost."""
#         InvoiceItem = apps.get_model("finance", "InvoiceItem")
#         max_cost_subq = (
#             InvoiceItem.objects
#             .filter(internal_part_number=OuterRef("pk"))
#             .values("internal_part_number")
#             .annotate(m=Max("unit_cost"))
#             .values("m")[:1]
#         )
#         return self.annotate(highest_invoice_cost=Subquery(max_cost_subq))
    
# InventoryMasterManager = models.Manager.from_queryset(InventoryMasterQuerySet)



#     # make all the common entry points accept the alias
#     def get(self, *args, **kwargs):
#         return super().get(*args, **self._alias_kwargs(kwargs))

#     def filter(self, *args, **kwargs):
#         return super().filter(*args, **self._alias_kwargs(kwargs))

#     def create(self, **kwargs):
#         return super().create(**self._alias_kwargs(kwargs))

#     def update_or_create(self, defaults=None, **kwargs):
#         return super().update_or_create(defaults=defaults, **self._alias_kwargs(kwargs))
    

# # -----------------------------
# # Models
# # -----------------------------
# class Vendor(models.Model):
#     name = models.CharField('Name', max_length=200)
#     address1 = models.CharField('Address 1', max_length=100, blank=True, null=True)
#     address2 = models.CharField('Adddress 2', max_length=100, blank=True, null=True)
#     city = models.CharField('City', max_length=100, blank=True, null=True)
#     state = models.CharField('State', max_length=100, blank=True, null=True)
#     zipcode = models.CharField('Zipcode', max_length=100, blank=True, null=True)
#     phone1 = models.CharField('Phone 1', max_length=100, blank=True, null=True)
#     phone2 = models.CharField('Phone 2', max_length=100, blank=True, null=True)
#     email = models.EmailField('Email', max_length=100, blank=True, null=True)
#     website = models.URLField('Website', max_length=100, blank=True, null=True)

#     supplier = models.BooleanField('Supplier', default=True)
#     retail_vendor = models.BooleanField('Retail Vendor', default=True)
#     inventory_vendor = models.BooleanField('Inventory Vendor', default=True)
#     online_store_vendor = models.BooleanField('Online Store Vendor', default=False)
#     non_inventory_vendor = models.BooleanField('Non Inventory Vendor', default=True)

#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
#     active = models.BooleanField(default=True)
#     void = models.BooleanField(default=False)

#     objects = VendorQuerySet.as_manager()

#     class Meta:
#         ordering = ("name",)

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("inventory:vendor_detail", kwargs={"id": self.id})
    
# class InventoryMaster(models.Model):
#     name = models.CharField('Name', max_length=200)
#     internal_part_number = models.CharField(max_length=64, blank=True, null=True, db_index=True)
#     is_active = models.BooleanField(default=True)
#     merged_into = models.ForeignKey('self', null=True, blank=True,
#                                     on_delete=models.SET_NULL, related_name='merged_children')
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     primary_vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL)
#     primary_vendor_part_number = models.CharField('Primary Vendor Part Number', max_length=100, blank=True, null=True)
#     primary_base_unit = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
#     units_per_base_unit = models.DecimalField('Units per base unit (almost always 1)', max_digits=15, decimal_places=6, blank=True, null=True)
#     unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, blank=True, null=True)
#     price_per_m = models.DecimalField('Price Per M', max_digits=15, decimal_places=4, blank=True, null=True)
#     supplies = models.BooleanField('Supply Item', default=True)
#     retail = models.BooleanField('Retail Item', default=True)
#     non_inventory = models.BooleanField('Non Inventory Item', default=False)
#     online_store = models.BooleanField('Online Store Item', default=True)
#     not_grouped = models.BooleanField('Not Price Grouped', default=False)
#     grouped = models.BooleanField('In price group', default=False)
#     #price_group = models.ManyToManyField(
#     #   GroupCategory,
#     #     through="inventory.InventoryPricingGroup",   # ← important
#     #     related_name="items",
#     #     blank=True,
#     # )
#     price_group = models.ManyToManyField(
#         'controls.GroupCategory',
#         through='inventory.InventoryPricingGroup',
#         through_fields=('inventory', 'group'),
#         related_name='items',
#         blank=True,
#     )
#     # price_group = models.ForeignKey('controls.PriceGroup', null=True, blank=True, on_delete=models.SET_NULL)
#     # price_groups_temp = models.ManyToManyField('controls.PriceGroup', blank=True, related_name='inventory_items_temp')
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
#     high_price = models.DecimalField('High Price', max_digits=15, decimal_places=6, blank=True, null=True)

#     objects = InventoryMasterManager()

#     def __str__(self):
#         return self.name
    
#     def add_to_price_group(self, group: 'GroupCategory') -> bool:
#         from .models import InventoryPricingGroup
#         InventoryPricingGroup.objects.get_or_create(inventory=self, group=group)
#         return True

#     def set_primary_vendor(self, vendor: 'Vendor', vendor_part_number: Optional[str] = None) -> bool:
#         self.primary_vendor = vendor
#         if vendor_part_number is not None:
#             self.primary_vendor_part_number = vendor_part_number
#         self.save(update_fields=["primary_vendor", "primary_vendor_part_number"])
#         return True

#     def set_primary_base_unit(self, unit: 'Measurement', qty: Decimal) -> bool:
#         self.primary_base_unit = unit
#         self.units_per_base_unit = qty
#         self.save(update_fields=["primary_base_unit", "units_per_base_unit"])
#         # ensure base variation exists, since tests check for it in another case
#         self.ensure_base_variation()
#         return True

#     def ensure_base_variation(self):
#         # idempotent: exactly one row for the master, with the base unit & qty
#         InventoryQtyVariations.objects.update_or_create(
#             inventory=self,                # FK to InventoryMaster (tests filter by this)
#             variation=self.primary_base_unit,
#             defaults={"variation_qty": self.units_per_base_unit},
#         )

#     def purchase_history(self):
#         """Newest invoices first for this master item."""
#         InvoiceItem = apps.get_model("finance", "InvoiceItem")
#         return (
#             InvoiceItem.objects
#             .filter(internal_part_number=self.pk)
#             .select_related("invoice", "vendor")  # if you show vendor, keep this
#             .order_by("-invoice__invoice_date")
#         )
    
#     class Meta:
#         constraints = [
#             models.CheckConstraint(
#                 check=Q(units_per_base_unit__gt=0),
#                 name="ipn_units_per_base_unit_gt_0",
#             ),
#         ]
    
class VendorItem(models.Model):
    """M2M through table that connects items to vendors + vendor SKU/prices."""
    item = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="vendor_item_links")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="vendor_item_links")
    vendor_sku = models.CharField(max_length=128, blank=True, null=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # unique per (vendor, item)
    class Meta:
        unique_together = [("vendor", "item")]

class PriceHistory(models.Model):
    item = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="price_history")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField(db_index=True)

class PurchaseLine(models.Model):
    item = models.ForeignKey(InventoryMaster, on_delete=models.PROTECT, related_name="purchase_lines")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    # …

# # class WorkorderItem(models.Model):
# #     inventory_item = models.ForeignKey(InventoryMaster, on_delete=models.PROTECT, related_name="wo_items")
# #     qty = models.DecimalField(max_digits=12, decimal_places=2)
# #     # …

class InventoryMergeLog(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    target = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="+")
    merged_ids = models.JSONField()                 # [int, int, …]
    details = models.JSONField(default=dict)        # per-model move map + snapshots
    previous_names = models.JSONField(default=dict) # {item_id: "old name"}
    note = models.TextField(blank=True, default="")


class VendorContact(models.Model):
    vendor = models.ForeignKey(
        Vendor, blank=True, null=True, on_delete=models.SET_NULL, related_name="contacts"
    )
    fname = models.CharField('First Name', max_length=100, blank=True, null=True)
    lname = models.CharField('Last Name', max_length=100, blank=True, null=True)
    phone1 = models.CharField('Phone', max_length=100, blank=True, null=True)
    email = models.EmailField('Email', max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("lname", "fname")

    def __str__(self) -> str:
        full = " ".join(filter(None, [self.fname, self.lname])).strip()
        who = full or (self.email or "Contact")
        org = f" @ {self.vendor.name}" if self.vendor else ""
        return f"{who}{org}"


class ItemPricingGroup(models.Model):
    name = models.CharField('Name', max_length=100)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("controls:view_price_group_detail", kwargs={"id": self.id})


#     # ---------- Convenience / query helpers ----------
#     def purchase_history(self):
#         """Used by item details; newest invoices first."""
#         InvoiceItem = apps.get_model("finance", "InvoiceItem")
#         return (
#             InvoiceItem.objects.filter(internal_part_number=self.pk)
#             .select_related("invoice")
#             .order_by("-invoice__invoice_date")
#         )

#     def highest_invoice_cost(self):
#         """Return highest unit_cost from finance.InvoiceItem, or None."""
#         InvoiceItem = apps.get_model("finance", "InvoiceItem")
#         agg = InvoiceItem.objects.filter(internal_part_number=self.pk).aggregate(Max("unit_cost"))
#         return agg["unit_cost__max"]

#     def update_high_price_from_invoices(self):
#         """Compute & persist highest invoice unit cost to high_price."""
#         value = self.highest_invoice_cost()
#         if value is not None:
#             self.high_price = value
#             self.save(update_fields=["high_price"])
#         return value

#     # ---------- State mutation helpers (idempotent) ----------
#     def ensure_base_variation(self) -> bool:
#         """
#         Ensure there is an InventoryQtyVariations row mirroring
#         primary_base_unit/units_per_base_unit. Returns True if created.
#         """
#         if not self.primary_base_unit_id or not self.units_per_base_unit:
#             return False
#         InventoryQtyVariations = apps.get_model("inventory", "InventoryQtyVariations")
#         _, created = InventoryQtyVariations.objects.get_or_create(
#             inventory=self,
#             variation=self.primary_base_unit,
#             defaults={"variation_qty": self.units_per_base_unit},
#         )
#         return created

#     @transaction.atomic
#     def set_primary_base_unit(self, unit, qty):
#         """
#         Set primary_base_unit + units_per_base_unit and ensure matching variation.
#         `unit` may be a Measurement instance or its pk. Returns self.
#         """
#         Measurement = apps.get_model("controls", "Measurement")
#         if isinstance(unit, (int, str)):
#             unit = Measurement.objects.get(pk=unit)
#         self.primary_base_unit = unit
#         self.units_per_base_unit = qty
#         self.save(update_fields=["primary_base_unit", "units_per_base_unit"])
#         self.ensure_base_variation()
#         return self

#     def set_units_per_base_unit(self, qty):
#         """Update only units_per_base_unit. Returns self."""
#         self.units_per_base_unit = qty
#         self.save(update_fields=["units_per_base_unit"])
#         return self

#     @transaction.atomic
#     def set_primary_vendor(self, vendor, vendor_part_number=None):
#         """
#         Set primary_vendor (and optional part number) and ensure VendorItemDetail exists.
#         `vendor` may be a Vendor instance or its pk. Returns self.
#         """
#         Vendor = apps.get_model("inventory", "Vendor")
#         VendorItemDetail = apps.get_model("inventory", "VendorItemDetail")
#         if isinstance(vendor, (int, str)):
#             vendor = Vendor.objects.get(pk=vendor)

#         fields = ["primary_vendor"]
#         self.primary_vendor = vendor
#         if vendor_part_number is not None:
#             self.primary_vendor_part_number = vendor_part_number
#             fields.append("primary_vendor_part_number")
#         self.save(update_fields=fields)

#         VendorItemDetail.objects.get_or_create(
#             internal_part_number=self,
#             vendor=vendor,
#             defaults={
#                 "name": self.name,
#                 "vendor_part_number": self.primary_vendor_part_number,
#                 "description": self.description or "",
#                 "supplies": self.supplies,
#                 "retail": self.retail,
#                 "non_inventory": self.non_inventory,
#                 "high_price": self.high_price,
#             },
#         )
#         return self

#     def add_to_price_group(self, group, high_price=None):
#         link, created = InventoryPricingGroup.objects.get_or_create(
#             inventory=self, group=group, defaults={"high_price": high_price}
#         )
#         if not created and high_price is not None and link.high_price != high_price:
#             link.high_price = high_price
#             link.save(update_fields=["high_price"])
#         if not self.grouped:
#             self.grouped = True
#             if hasattr(self, "not_grouped"):
#                 self.not_grouped = False
#             self.save(update_fields=[f for f in ("grouped", "not_grouped") if hasattr(self, f)])
#         return link
    
#     def remove_from_price_group(self, group):
#         InventoryPricingGroup.objects.filter(inventory=self, group=group).delete()
#         has_links = InventoryPricingGroup.objects.filter(inventory=self).exists()
#         updates = {}
#         if self.grouped != has_links:
#             updates["grouped"] = has_links
#         if hasattr(self, "not_grouped"):
#             updates["not_grouped"] = False if has_links else (self.not_grouped or False)
#         if updates:
#             for k, v in updates.items():
#                 setattr(self, k, v)
#             self.save(update_fields=list(updates))

#     # Backward-compat alias (legacy code may rely on this name)
#     def add_to_group(self, group):
#         return self.add_to_price_group(group)


# class InventoryPricingGroup(models.Model):
#     inventory = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="group_links",)
#     group = models.ForeignKey(GroupCategory, on_delete=models.CASCADE, related_name="item_links",)
#     high_price = models.DecimalField('High Price', max_digits=15, decimal_places=4, blank=True, null=True)

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['inventory', 'group'], name='uniq_inventory_group_once')
#         ]
#         indexes = [
#             models.Index(fields=['inventory']), 
#             models.Index(fields=['group']),
#         ]

#     def __str__(self) -> str:
#         return f"{self.inventory} ↔ {self.group}"

#     def get_absolute_url(self):
#         return reverse("controls:view_price_group_detail", kwargs={"id": self.group.id})


# class InventoryQtyVariationsQuerySet(models.QuerySet):
#     def distinct_inventories(self):
#         """
#         Return one (earliest pk) variation per InventoryMaster.
#         Produces a queryset of InventoryQtyVariations model instances.
#         """
#         sub = (
#             self.values("inventory_id")
#             .annotate(min_pk=Min("pk"))
#             .values_list("min_pk", flat=True)
#         )
#         return self.filter(pk__in=list(sub))


# class InventoryQtyVariations(models.Model):
#     inventory = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE)
#     variation = models.ForeignKey(Measurement, null=True, on_delete=models.SET_NULL)
#     variation_qty = models.DecimalField('Variation Qty', max_digits=15, decimal_places=4)

#     objects = InventoryQtyVariationsQuerySet.as_manager()

#     class Meta:
#         indexes = [
#             models.Index(fields=['inventory']),
#             models.Index(fields=['variation']),
#         ]

#     def __str__(self) -> str:
#         return f"{self.inventory.name} — {self.variation} = {self.variation_qty}"

#     def get_absolute_url(self):
#         return reverse("inventory:item_variation_details", kwargs={"id": self.inventory.id})


# # @receiver(post_save, sender=InventoryMaster)
# # def Unit_Cost_Handler(sender, instance, created, *args, **kwargs):
# #     """
# #     When high_price and units_per_base_unit are set on InventoryMaster,
# #     update Unit Cost and Price per M on both master and legacy Inventory.
# #     """
# #     if instance.high_price and instance.units_per_base_unit:
# #         unit_cost = Decimal(instance.high_price) / instance.units_per_base_unit
# #         m = unit_cost * 1000
# #         unit_cost = round(unit_cost, 6)
# #         m = round(m, 6)
# #         InventoryMaster.objects.filter(pk=instance.pk).update(
# #             unit_cost=unit_cost, price_per_m=m, updated=timezone.now()
# #         )
# #         Inventory.objects.filter(master=instance.pk).update(
# #             unit_cost=unit_cost, price_per_m=m, updated=timezone.now()
# #         )


# class Inventory(models.Model):
#     master = models.ForeignKey('InventoryMaster', on_delete=models.CASCADE, related_name='inventories',
#                                null=True, blank=True, db_index=True)
#     name = models.CharField('Name', max_length=100)
#     name2 = models.CharField('Additional Name', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
#     unit_cost = models.DecimalField('Unit Cost', max_digits=15, decimal_places=4, null=True, blank=True)
#     price_per_m = models.DecimalField('Price Per M', max_digits=15, decimal_places=4, null=True, blank=True)
#     price_per_sqft = models.CharField('Price per SqFt', max_length=100, blank=True, null=True)
#     current_stock = models.CharField('Current Stock', max_length=100, blank=True, null=True)
#     color = models.CharField('Color', max_length=100, blank=True, null=True)
#     size = models.CharField('Size', max_length=100, blank=True, null=True)
#     width = models.CharField('Width', max_length=100, blank=True, null=True)
#     width_measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='width_mea')
#     length = models.CharField('Length', max_length=100, blank=True, null=True)
#     length_measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='length_mea')
#     measurement = models.ForeignKey(Measurement, blank=True, null=True, on_delete=models.DO_NOTHING)
#     type_paper = models.BooleanField('Paper', default=False)
#     type_envelope = models.BooleanField('Envelope', default=False)
#     type_wideformat = models.BooleanField('Wide Format', default=False)
#     type_vinyl = models.BooleanField('Vinyl', default=False)
#     type_mask = models.BooleanField('Mask', default=False)
#     type_laminate = models.BooleanField('Laminate', default=False)
#     type_substrate = models.BooleanField('Substrate', default=False)
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
#     inventory_category = models.ManyToManyField(InventoryCategory)
#     retail_item = models.BooleanField('Retail Item', default=True)

#     objects = InventoryManager()

#     # allow Inventory(internal_part_number=...) constructor calls, too
#     def __init__(self, *args, **kwargs):
#         if 'internal_part_number' in kwargs:
#             kwargs['master'] = kwargs.pop('internal_part_number')
#         super().__init__(*args, **kwargs)

#     def purchase_history(self):
#         if self.master_id:
#             return self.master.purchase_history()
#         InvoiceItem = apps.get_model("finance", "InvoiceItem")
#         return InvoiceItem.objects.none()

#     # read-only property so templates/old code can still access it
#     @property
#     def internal_part_number(self):
#         return self.master

#     @property
#     def unit_cost_effective(self):
#         return self.unit_cost if self.unit_cost is not None else getattr(self.master, "unit_cost", None)

#     @property
#     def price_per_m_effective(self):
#         return self.price_per_m if self.price_per_m is not None else getattr(self.master, "price_per_m", None)

#     def __str__(self) -> str:
#         return self.name or f"Inventory #{self.pk}"


# class VendorItemDetail(models.Model):
#     vendor = models.ForeignKey(Vendor, null=True, on_delete=models.CASCADE)
#     name = models.CharField('Name', max_length=100)
#     vendor_part_number = models.CharField('Vendor Part Number', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     internal_part_number = models.ForeignKey(InventoryMaster, on_delete=models.CASCADE, related_name="vendor_items")
#     supplies = models.BooleanField('Supply Item')
#     retail = models.BooleanField('Retail Item')
#     non_inventory = models.BooleanField('Non Inventory Item')
#     online_store = models.BooleanField('Online Store Item')
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
#     high_price = models.DecimalField('High Price', max_digits=15, decimal_places=4, blank=True, null=True)

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["internal_part_number", "vendor"],
#                 name="uq_vendor_detail_once_per_vendor",
#             )
#         ]

#     def __str__(self) -> str:
#         vend = self.vendor.name if self.vendor else "Unknown vendor"
#         return f"{vend} → {self.internal_part_number.name}"

# class InternalCompany(models.TextChoices):
#     LK = "LK Design", "LK Design"
#     KRUEGER = "Krueger Printing", "Krueger Printing"
#     OFFICE = "Office Supplies", "Office Supplies"

# class OrderOut(models.Model):
#     workorder = models.ForeignKey(Workorder, blank=False, null=True, on_delete=models.CASCADE)
#     hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
#     workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
#     internal_company = models.CharField('Internal Company', max_length=32, choices=InternalCompany.choices)
#     customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL)
#     hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
#     category = models.CharField('Category', max_length=10, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)

#     vendor = models.ForeignKey('Vendor', blank=True, null=True, on_delete=models.SET_NULL)
#     purchase_price = models.DecimalField('Purchase Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     percent_markup = models.DecimalField('Percent Markup', max_digits=8, decimal_places=2, blank=True, null=True)
#     quantity = models.DecimalField('Quantity', max_digits=8, decimal_places=2, blank=True, null=True)
#     unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
#     total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
#     last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
#     notes = models.TextField('Notes:', blank=True, null=False)
#     dateentered = models.DateTimeField(auto_now_add=True)
#     open = models.BooleanField(default=False, db_index=True)
#     billed = models.BooleanField('Billed', default=False, db_index=True)
#     edited = models.BooleanField('Edited', default=False)

#     objects = OrderOutQuerySet.as_manager()

#     def save(self, *args, **kwargs):
#         # If it's billed, force it closed to avoid DB-level check explosions
#         return super().save(*args, **kwargs)

#     def clean(self):
#         if self.open and self.billed:
#             raise ValidationError("OrderOut cannot be both open and billed.")

#     class Meta:
#         ordering = ["-dateentered"]
#         indexes = [
#             models.Index(fields=["billed"]),
#             models.Index(fields=["dateentered"]),
#             models.Index(fields=["vendor", "dateentered"]),
#         ]
#         constraints = [
#             # cannot be open AND billed at the same time
#             models.CheckConstraint(
#                 check=~(Q(open=True) & Q(billed=True)),
#                 name="oo_not_both_open_and_billed",
#             ),
#             # non-negative or NULL
#             models.CheckConstraint(
#                 check=(Q(purchase_price__gte=0) | Q(purchase_price__isnull=True)),
#                 name="oo_purchase_price_nonneg",
#             ),
#             models.CheckConstraint(
#                 check=(Q(percent_markup__gte=0) | Q(percent_markup__isnull=True)),
#                 name="oo_percent_markup_nonneg",
#             ),
#             models.CheckConstraint(
#                 check=(Q(quantity__gte=0) | Q(quantity__isnull=True)),
#                 name="oo_quantity_nonneg",
#             ),
#             models.CheckConstraint(
#                 check=(Q(unit_price__gte=0) | Q(unit_price__isnull=True)),
#                 name="oo_unit_price_nonneg",
#             ),
#             models.CheckConstraint(
#                 check=(Q(total_price__gte=0) | Q(total_price__isnull=True)),
#                 name="oo_total_price_nonneg",
#             ),
#         ]

#     def __str__(self) -> str:
#         return f"OrderOut #{self.pk} to {(self.vendor.name if self.vendor else 'Unknown Vendor')}"


# class SetPrice(models.Model):
#     name = models.CharField('Name', max_length=100, blank=True, null=True)
#     workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
#     hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
#     workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
#     internal_company = models.CharField(
#         'Internal Company',
#         choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')],
#         max_length=100,
#     )
#     customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
#     hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
#     category = models.CharField('Category', max_length=10, blank=True, null=True)
#     setprice_category = models.CharField('Item Category', max_length=10, blank=True, null=True)
#     setprice_item = models.CharField('Item', max_length=10, blank=True, null=True)
#     setprice_qty = models.CharField('Pieces / set', max_length=10, blank=True, null=True)
#     setprice_price = models.CharField('Price / set', max_length=10, blank=True, null=True)
#     total_pieces = models.CharField('Total pieces', max_length=10, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     paper_stock = models.ForeignKey('Inventory', blank=True, null=True, on_delete=models.SET_NULL)
#     side_1_inktype = models.CharField(
#         'Side 1 Ink',
#         choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')],
#         max_length=100, blank=True, null=True
#     )
#     side_2_inktype = models.CharField(
#         'Side 2 Ink',
#         choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')],
#         max_length=100, blank=True, null=True
#     )
#     quantity = models.PositiveIntegerField('Quantity', blank=True, null=True)
#     unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
#     total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
#     last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
#     notes = models.TextField('Notes:', blank=True, null=False)
#     dateentered = models.DateTimeField(auto_now_add=True)
#     billed = models.BooleanField('Billed', default=False)
#     edited = models.BooleanField('Edited', default=False)

#     def __str__(self):
#         return self.workorder.workorder


# class Photography(models.Model):
#     workorder = models.ForeignKey(Workorder, max_length=100, blank=False, null=True, on_delete=models.CASCADE)
#     hr_workorder = models.CharField('Human Readable Workorder', max_length=100, blank=True, null=True)
#     workorder_item = models.CharField('Workorder Item', max_length=100, blank=True, null=True)
#     internal_company = models.CharField(
#         'Internal Company',
#         choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing'), ('Office Supplies', 'Office Supplies')],
#         max_length=100,
#     )
#     customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_DEFAULT, default=2)
#     hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True)
#     category = models.CharField('Category', max_length=10, blank=True, null=True)
#     subcategory = models.CharField('Subcategory', max_length=10, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)

#     quantity = models.DecimalField('Quantity', max_digits=6, decimal_places=2, blank=True, null=True)
#     unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
#     total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
#     last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
#     last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
#     notes = models.TextField('Notes:', blank=True, null=False)
#     dateentered = models.DateTimeField(auto_now_add=True)
#     billed = models.BooleanField('Billed', default=False)
#     edited = models.BooleanField('Edited', default=False)


# # # Create a legacy Inventory row when an InventoryMaster is saved (if missing)
# # # Use your centralized rounding helpers if available
# # try:
# #     from lib.pricing import quantize_money, quantize_rate_m  # adapt names if different
# # except Exception:
# #     # Safe fallbacks: 6-decimal money, 6-decimal per-thousand rate
# #     def quantize_money(value: Decimal) -> Decimal:
# #         return value.quantize(Decimal("0.000001"))
# #     def quantize_rate_m(value: Decimal) -> Decimal:
# #         return value.quantize(Decimal("0.000001"))

# def _str6(d: Optional[Decimal]) -> str:
#     """Inventory.unit_cost / price_per_m are CharFields; render with fixed scale."""
#     if d is None:
#         return ""
#     return f"{d:.6f}"

# @receiver(post_save, sender=InventoryMaster)
# def recompute_and_sync_pricing(sender, instance: InventoryMaster, created, **kwargs):
#     """
#     - If high_price & units_per_base_unit are set, recompute unit_cost and price_per_m.
#     - Persist computed numbers to InventoryMaster (manager .update() to avoid recursion).
#     - Ensure/sync the Inventory shadow row (strings for cost fields).
#     - Run on_commit to avoid race conditions.
#     """
#     def _do():
#         unit_cost_dec: Optional[Decimal] = None
#         per_m_dec: Optional[Decimal] = None

#         if instance.high_price and instance.units_per_base_unit:
#             # Compute prices
#             unit_cost_dec = quantize_money(
#                 Decimal(instance.high_price) / Decimal(instance.units_per_base_unit)
#             )
#             per_m_dec = quantize_rate_m(unit_cost_dec * Decimal("1000"))

#             # Update numeric fields on master without firing signals again
#             InventoryMaster.objects.filter(pk=instance.pk).update(
#                 unit_cost=unit_cost_dec,
#                 price_per_m=per_m_dec,
#                 updated=timezone.now(),
#             )

#         # Upsert the shadow Inventory row
#         inv, _created = Inventory.objects.get_or_create(
#             internal_part_number=instance,   # alias handled by InventoryManager/__init__
#             defaults={
#                 "name": instance.name,
#                 "description": instance.description or "",
#                 "unit_cost": unit_cost_dec,
#                 "price_per_m": per_m_dec,
#                 "measurement": instance.primary_base_unit,
#                 "retail_item": instance.retail,
#             },
#         )

#         # Keep a minimal set of fields in sync (avoid clobbering user-edited pricing)
#         updates = {}
#         if inv.name != instance.name:
#             updates["name"] = instance.name
#         if (inv.description or "") != (instance.description or ""):
#             updates["description"] = instance.description or ""
#         if inv.measurement_id != instance.primary_base_unit_id:
#             updates["measurement_id"] = instance.primary_base_unit_id
#         if inv.retail_item != instance.retail:
#             updates["retail_item"] = instance.retail

#         # Only update string pricing if we recomputed it now
#         if unit_cost_dec is not None and inv.unit_cost != unit_cost_dec:
#             updates["unit_cost"] = unit_cost_dec
#         if per_m_dec is not None and inv.price_per_m != per_m_dec:
#             updates["price_per_m"] = per_m_dec

#         if updates:
#             updates["updated"] = timezone.now()
#             Inventory.objects.filter(pk=inv.pk).update(**updates)

#     transaction.on_commit(_do)

