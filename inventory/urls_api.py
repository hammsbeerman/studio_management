from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import InventoryMasterViewSet

router = DefaultRouter()
router.register(r"inventory-master", InventoryMasterViewSet, basename="inventory-master")

urlpatterns = [
    path("", include(router.urls)),
]