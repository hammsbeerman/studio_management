from rest_framework import serializers
from .models import Inventory, InventoryMaster, InventoryQtyVariations, Vendor, GroupCategory

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'name', 'description']

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
    
class InventoryMasterLiteSerializer(serializers.ModelSerializer):
    primary_vendor_name = serializers.CharField(source="primary_vendor.name", read_only=True)
    primary_base_unit_name = serializers.CharField(source="primary_base_unit.name", read_only=True)

    class Meta:
        model = InventoryMaster
        fields = [
            "id",
            "name",
            "description",
            "unit_cost",
            "price_per_m",
            "high_price",
            "primary_vendor",
            "primary_vendor_name",
            "primary_vendor_part_number",
            "primary_base_unit",
            "primary_base_unit_name",
            "units_per_base_unit",
            "supplies",
            "retail",
            "non_inventory",
            "online_store",
            "grouped",
            "not_grouped",
            "created",
            "updated",
        ]
        read_only_fields = ["created", "updated"]

class GroupCategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupCategory
        fields = ["id", "name"]


class InventoryMasterSerializer(InventoryMasterLiteSerializer):
    # IDs of groups (useful for write-less API)
    price_group = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )
    # Friendly names too
    price_group_names = GroupCategoryMiniSerializer(
        source="price_group", many=True, read_only=True
    )

    class Meta(InventoryMasterLiteSerializer.Meta):
        fields = InventoryMasterLiteSerializer.Meta.fields + [
            "price_group",
            "price_group_names",
        ]


## This entire page is solely for testing API data