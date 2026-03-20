from django.conf import settings
from django.db import models


class ArchiveAssetOverlay(models.Model):
    ASSET_ROLE_CHOICES = [
        ("reference", "Reference"),
        ("source", "Source"),
        ("proof", "Proof"),
        ("print_ready", "Print Ready"),
        ("other", "Other"),
    ]

    archive_item_id = models.CharField(max_length=36, db_index=True)
    archive_filename = models.CharField(max_length=500, blank=True, default="")
    archive_path = models.TextField(blank=True, default="")
    archive_hash = models.CharField(max_length=64, blank=True, default="")
    customer = models.ForeignKey("customers.Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="archive_assets")
    workorder = models.ForeignKey("workorders.Workorder", null=True, blank=True, on_delete=models.SET_NULL, related_name="archive_assets")
    asset_role = models.CharField(max_length=30, choices=ASSET_ROLE_CHOICES, default="reference")
    print_ready = models.BooleanField(default=False)
    official_asset = models.BooleanField(default=False)
    reuse_approved = models.BooleanField(default=False)
    do_not_use = models.BooleanField(default=False)
    notes_summary = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_archive_overlays")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["archive_item_id"]),
            models.Index(fields=["customer", "workorder"]),
        ]

    def __str__(self):
        return self.archive_filename or self.archive_item_id


class ArchiveAssetTag(models.Model):
    overlay = models.ForeignKey(ArchiveAssetOverlay, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=100, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("overlay", "name")]

    def __str__(self):
        return self.name


class ArchiveAssetNote(models.Model):
    overlay = models.ForeignKey(ArchiveAssetOverlay, on_delete=models.CASCADE, related_name="notes")
    note = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Note for {self.overlay_id}"
