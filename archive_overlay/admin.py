from django.contrib import admin

from .models import ArchiveAssetNote, ArchiveAssetOverlay, ArchiveAssetTag

admin.site.register(ArchiveAssetOverlay)
admin.site.register(ArchiveAssetTag)
admin.site.register(ArchiveAssetNote)
