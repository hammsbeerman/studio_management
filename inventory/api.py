from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import InventoryMaster
from .serializers import InventoryMasterLiteSerializer, InventoryMasterSerializer

class InventoryMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        InventoryMaster.objects
        .select_related("primary_vendor", "primary_base_unit")
        .prefetch_related("price_group")
        .all()
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = InventoryMasterLiteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filter by exact matches; add/remove as needed
    filterset_fields = {
        "primary_vendor": ["exact"],
        "grouped": ["exact"],
        "online_store": ["exact"],
        "non_inventory": ["exact"],
        "supplies": ["exact"],
        "retail": ["exact"],
        "price_group": ["exact"],  # works with M2M
    }
    search_fields = ["name", "description", "primary_vendor_part_number"]
    ordering_fields = ["name", "updated", "created", "unit_cost", "high_price", "price_per_m"]
    ordering = ["name"]

    def get_serializer_class(self):
        # Lite for list, full for retrieve
        return InventoryMasterLiteSerializer if self.action == "list" else InventoryMasterSerializer