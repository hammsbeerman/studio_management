from __future__ import annotations

from decimal import Decimal
from typing import Optional, Union

from django.db import models, transaction
from django.db.models import F, Q
from django.urls import reverse


# -------------------------------
# QuerySets / Managers
# -------------------------------

class CategoryQuerySet(models.QuerySet):
    def active(self) -> "CategoryQuerySet":
        return self.filter(active=True)

    def inactive(self) -> "CategoryQuerySet":
        return self.filter(active=False)

    def wideformat(self) -> "CategoryQuerySet":
        return self.filter(wideformat=True)

    def setprice(self) -> "CategoryQuerySet":
        return self.filter(setprice=True)

    def with_template(self) -> "CategoryQuerySet":
        return self.filter(template=True)

    def for_inventory_category(self, inv_cat: Optional[Union[int, "InventoryCategory"]],
) -> "CategoryQuerySet":
        if inv_cat is None:
            return self.filter(inventory_category__isnull=True)
        if isinstance(inv_cat, int):
            return self.filter(inventory_category_id=inv_cat)
        return self.filter(inventory_category=inv_cat)


CategoryManager = models.Manager.from_queryset(CategoryQuerySet)


class RetailInventoryCategoryQuerySet(models.QuerySet):
    def active(self) -> "RetailInventoryCategoryQuerySet":
        return self.filter(active=True)

    def top_level(self) -> "RetailInventoryCategoryQuerySet":
        # parent is a CharField in current schema; treat null/empty as top-level
        return self.filter(Q(parent__isnull=True) | Q(parent=""))


RetailInventoryCategoryManager = models.Manager.from_queryset(RetailInventoryCategoryQuerySet)


class RetailInventorySubCategoryQuerySet(models.QuerySet):
    def active(self) -> "RetailInventorySubCategoryQuerySet":
        return self.filter(active=True)


RetailInventorySubCategoryManager = models.Manager.from_queryset(RetailInventorySubCategoryQuerySet)

def add_to_group(self, group_or_id):
    from django.apps import apps
    InventoryPricingGroup = apps.get_model('inventory', 'InventoryPricingGroup')
    group_id = getattr(group_or_id, 'id', group_or_id)
    InventoryPricingGroup.objects.get_or_create(group_id=group_id, inventory=self)

def add_to_price_group(self, group_or_id):
    return self.add_to_group(group_or_id)


# -------------------------------
# Models
# -------------------------------

class Numbering(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False, unique=True)
    value = models.PositiveIntegerField('Value', blank=False, null=False)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @transaction.atomic
    def bump(self, step: int = 1) -> int:
        """
        Atomically increment the counter and return the new value.
        """
        Numbering.objects.filter(pk=self.pk).update(value=F("value") + step)
        self.refresh_from_db(fields=["value"])
        return self.value

    @transaction.atomic
    def next_value(self) -> int:
        """Convenience alias for bump(1)."""
        return self.bump(1)


class FixedCost(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False, unique=True)
    create_workorder = models.DecimalField('Create Workorder', max_digits=10, decimal_places=2, blank=True, null=True)
    reclaim_artwork = models.DecimalField('Reclaim Artwork', max_digits=10, decimal_places=2, blank=True, null=True)
    send_to_press = models.DecimalField('Send to press', max_digits=10, decimal_places=2, blank=True, null=True)
    send_mailmerge_to_press = models.DecimalField('Send Mailmerge to press', max_digits=10, decimal_places=2, blank=True, null=True)
    material_markup = models.DecimalField('Material Markup Percentage', max_digits=10, decimal_places=2, blank=True, null=True)
    wear_and_tear = models.DecimalField('Wear and Tear', max_digits=10, decimal_places=2, blank=True, null=True)
    trim_to_size = models.DecimalField('Trim to Size', max_digits=10, decimal_places=2, blank=True, null=True)
    # Duplo
    duplo_1 = models.DecimalField('Duplo1', max_digits=10, decimal_places=2, blank=True, null=True)
    duplo_2 = models.DecimalField('Duplo2', max_digits=10, decimal_places=2, blank=True, null=True)
    duplo_3 = models.DecimalField('Duplo3', max_digits=10, decimal_places=2, blank=True, null=True)
    # Compounds
    ncr_compound = models.DecimalField('NCR Compound', max_digits=10, decimal_places=2, blank=True, null=True)
    pad_compound = models.DecimalField('Padding Compound', max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Fixed costs"

    def __str__(self) -> str:
        return self.name


class InventoryCategory(models.Model):
    name = models.CharField('Name', max_length=100, null=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class GroupCategory(models.Model):
    name = models.CharField('Name', max_length=100, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("controls:view_price_group_detail", kwargs={"id": self.id})
    
class GroupLink(models.Model):
    """Through table: links a GroupCategory to an InventoryMaster."""
    category = models.ForeignKey('controls.GroupCategory', on_delete=models.CASCADE, related_name='links')
    item = models.ForeignKey('inventory.InventoryMaster', on_delete=models.CASCADE, related_name='group_links')

    class Meta:
        unique_together = (('category', 'item'),)
    
class ActiveCategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

class Category(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    design_type = models.BooleanField('Design Type', blank=True, null=True)

    formname = models.CharField('Form', max_length=100, blank=True, null=True)
    modelname = models.CharField('Model', max_length=100, blank=True, null=True)
    modal = models.BooleanField('Popup Modal', blank=True, null=True, default=False)
    setprice = models.BooleanField('Is setprice category', blank=False, null=True, default=False)
    material_type = models.CharField('Material Type', max_length=100, blank=True, null=True)
    template = models.BooleanField('Template', blank=True, null=True, default=False)
    customform = models.BooleanField('Uses Custom Form', blank=True, null=True, default=False)
    pricesheet_type = models.ForeignKey(FixedCost, blank=True, null=True, on_delete=models.SET_NULL)
    inventory_category = models.ForeignKey(InventoryCategory, blank=True, null=True, on_delete=models.DO_NOTHING)
    wideformat = models.BooleanField('Wide Format', blank=False, null=True, default=False)
    active = models.BooleanField('Active', blank=True, null=True, default=True)

    objects = ActiveCategoryQuerySet.as_manager()

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""

    # Handy shorthands for templates/views (no schema changes)
    @property
    def is_active(self) -> bool:
        return bool(self.active)

    @property
    def is_setprice(self) -> bool:
        return bool(self.setprice)

    @property
    def is_wideformat(self) -> bool:
        return bool(self.wideformat)


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category, blank=False, null=True, on_delete=models.SET_NULL, related_name="Category"
    )
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    template = models.BooleanField('Template', blank=True, null=True, default=False)
    set_price = models.BooleanField('Is setprice category', blank=False, null=True, default=False)
    setprice_name = models.CharField('Name', max_length=100, blank=True, null=True)
    inventory_category = models.ForeignKey(InventoryCategory, blank=True, null=True, on_delete=models.DO_NOTHING)

    class Meta:
        # Avoid dupes under same Category
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="uniq_subcategory_per_category"
            )
        ]

    def __str__(self):
        return self.name or ""

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)

        # If the parent Category is a "setprice" category, enforce flags and ensure a matching SetPriceCategory
        if self.category and self.category.setprice:
            updates = {}
            if not self.set_price:
                updates["set_price"] = True
            if not self.setprice_name:
                updates["setprice_name"] = self.name

            if updates:
                SubCategory.objects.filter(pk=self.pk).update(**updates)

            from .models import SetPriceCategory  # local import to avoid cycles
            # Avoid duplicates if saved multiple times
            SetPriceCategory.objects.get_or_create(
                category=self.category,
                name=self.name or "",
                defaults={"updated": None},
            )


class SetPriceCategory(models.Model):
    category = models.ForeignKey(Category, blank=False, null=True, on_delete=models.SET_NULL)
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now=False, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="uniq_setpricecategory_per_category"
            )
        ]

    def __str__(self):
        return self.name


class DesignType(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class PostageType(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class SetPriceItemPrice(models.Model):
    # Field is called 'name' in the schema; keep to avoid a breaking migration.
    name = models.ForeignKey(SetPriceCategory, max_length=100, blank=True, null=True, on_delete=models.DO_NOTHING)
    description = models.CharField('Description', max_length=100, blank=False, null=False)
    set_quantity = models.DecimalField('Quantity / Order', max_digits=10, decimal_places=2, blank=False, null=False)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now=False, blank=True, null=True)

    class Meta:
        ordering = ("description",)

    def __str__(self) -> str:
        return self.description


class Measurement(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=True)
    abbreviation = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class JobStatus(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=True)
    icon = models.ImageField(null=True, blank=True, upload_to="jobstatus/")
    workorder_type = models.BooleanField('Workorder Type', blank=True, null=True, default=False)
    workorder_item_type = models.BooleanField('Workorder Item Type', blank=True, null=True, default=False)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class UserGroup(models.Model):
    name = models.CharField('Name', max_length=100, null=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class PaymentType(models.Model):
    name = models.CharField('Name', max_length=100, null=True)
    detail_field = models.CharField('Detail Field', max_length=100, blank=True, null=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""


class RetailInventoryCategory(models.Model):
    name = models.CharField('Name', max_length=100, null=True)
    icon = models.ImageField(null=True, blank=True, upload_to="retail_category")
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    active = models.BooleanField('Active', blank=True, null=True, default=True)
    # parent is a CharField in current schema; keeping as-is to avoid a migration
    parent = models.CharField('Parent Category', max_length=10, null=True)

    objects = RetailInventoryCategoryManager()

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""

    def get_subcat_url(self):
        return reverse("retail:subcat", kwargs={"cat": self.pk})

    def get_parent_url(self):
        return reverse("retail:parent", kwargs={"cat": self.parent})


class RetailInventorySubCategory(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    icon = models.ImageField(null=True, blank=True, upload_to="retail_category")
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    inventory_category = models.ManyToManyField(RetailInventoryCategory)
    active = models.BooleanField('Active', blank=True, null=True, default=True)

    objects = RetailInventorySubCategoryManager()

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or ""