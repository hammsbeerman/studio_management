from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.db.models import OuterRef, Exists, CharField
from django.db.models.functions import Cast

from finance.models import InvoiceItem
from inventory.models import InventoryLedger


def backfill_invoiceitem_ledger_locked(*, force: bool = False):
    """
    Backfill InvoiceItem.ledger_locked=True when InventoryLedger has AP_RECEIPT* rows for that item.

    Returns dict: { "updated": int, "marker": str }
    Raises RuntimeError if already ran (marker exists) unless force=True.
    """
    base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    marker_dir = base_dir / "backfills"
    marker_file = marker_dir / "invoiceitem_ledger_locked.done"

    if marker_file.exists() and not force:
        raise RuntimeError(
            f"Already ran. Marker exists at {marker_file}. "
            f"Delete marker or run with force."
        )

    marker_dir.mkdir(parents=True, exist_ok=True)

    ledger_exists_qs = InventoryLedger.objects.filter(
        source_type__startswith="AP_RECEIPT",
        source_id=Cast(OuterRef("pk"), output_field=CharField()),
    )

    qs = InvoiceItem.objects.filter(ledger_locked=False).filter(Exists(ledger_exists_qs))

    with transaction.atomic():
        updated = qs.update(ledger_locked=True)

    marker_file.write_text(f"Backfill complete.\nUpdated: {updated}\n")

    return {"updated": updated, "marker": str(marker_file)}