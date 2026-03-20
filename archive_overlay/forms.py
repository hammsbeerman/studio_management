from django import forms

from .models import ArchiveAssetNote, ArchiveAssetOverlay


class ArchiveAssetOverlayForm(forms.ModelForm):
    class Meta:
        model = ArchiveAssetOverlay
        fields = [
            "customer",
            "workorder",
            "asset_role",
            "print_ready",
            "official_asset",
            "reuse_approved",
            "do_not_use",
            "notes_summary",
        ]
        widgets = {
            "notes_summary": forms.Textarea(attrs={"rows": 3}),
        }


class ArchiveAssetNoteForm(forms.ModelForm):
    class Meta:
        model = ArchiveAssetNote
        fields = ["note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}
