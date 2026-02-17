from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import InventoryMaster, InventoryQtyVariations, Measurement


ONE = Decimal("1.0000")


@dataclass
class Change:
    item_id: int
    item_name: str
    action: str


def _pick_each_measurement() -> Measurement:
    # Prefer an existing "Each" (case-insensitive). Create if missing.
    m = Measurement.objects.filter(name__iexact="Each").first()
    if m:
        return m
    return Measurement.objects.create(name="Each")


def _choose_base_variation(item: InventoryMaster) -> Optional[InventoryQtyVariations]:
    """
    Choose the best candidate to be base UOM:
    - Prefer active + variation_qty == 1
    - Otherwise any active
    - Otherwise any at all
    """
    qs = item.variations.all().order_by("-active", "variation_qty", "id")

    # active + qty==1
    v = qs.filter(active=True, variation_qty=ONE).first()
    if v:
        return v

    # active anything
    v = qs.filter(active=True).first()
    if v:
        return v

    # anything
    return qs.first()


def _ensure_base_variation(
    item: InventoryMaster, each: Measurement, changes: List[Change], dry_run: bool
) -> InventoryQtyVariations:
    """
    Ensure exactly one base unit variation exists and is active and qty==1.
    If none exists, create one using:
      - item.primary_base_unit if set
      - else "Each"
    """
    base_flags = item.variations.filter(is_base_unit=True)
    if base_flags.count() == 1:
        v = base_flags.first()
        assert v is not None
        # base must be active and qty==1
        need_save = False
        if v.variation_qty != ONE:
            changes.append(Change(item.id, item.name, f"BASE qty {v.variation_qty} -> 1.0000 (id={v.id})"))
            if not dry_run:
                v.variation_qty = ONE
            need_save = True
        if not v.active:
            changes.append(Change(item.id, item.name, f"BASE set active=True (id={v.id})"))
            if not dry_run:
                v.active = True
            need_save = True
        if need_save and not dry_run:
            v.save(update_fields=["variation_qty", "active"])
        return v

    if base_flags.count() > 1:
        # Pick one, unset others
        chosen = base_flags.filter(active=True, variation_qty=ONE).first() or _choose_base_variation(item)
        if chosen is None:
            chosen = _create_base_from_legacy(item, each, changes, dry_run)
            return chosen

        for other in base_flags.exclude(pk=chosen.pk):
            changes.append(Change(item.id, item.name, f"Unset extra BASE flag (id={other.id})"))
            if not dry_run:
                other.is_base_unit = False
                other.save(update_fields=["is_base_unit"])

        # Normalize chosen
        need_save = False
        if chosen.variation_qty != ONE:
            changes.append(Change(item.id, item.name, f"BASE qty {chosen.variation_qty} -> 1.0000 (id={chosen.id})"))
            if not dry_run:
                chosen.variation_qty = ONE
            need_save = True
        if not chosen.active:
            changes.append(Change(item.id, item.name, f"BASE set active=True (id={chosen.id})"))
            if not dry_run:
                chosen.active = True
            need_save = True
        if not chosen.is_base_unit:
            changes.append(Change(item.id, item.name, f"Set BASE flag on chosen (id={chosen.id})"))
            if not dry_run:
                chosen.is_base_unit = True
            need_save = True

        if need_save and not dry_run:
            chosen.save(update_fields=["variation_qty", "active", "is_base_unit"])
        return chosen

    # No base flag set — try to infer or create
    # Prefer an existing qty==1 using legacy primary_base_unit if present
    if item.primary_base_unit_id:
        v = item.variations.filter(variation=item.primary_base_unit, variation_qty=ONE).first()
        if v:
            changes.append(Change(item.id, item.name, f"Set BASE flag using primary_base_unit (id={v.id})"))
            if not dry_run:
                v.is_base_unit = True
                if not v.active:
                    v.active = True
                v.save(update_fields=["is_base_unit", "active"])
            return v

    # Else pick a best candidate and normalize it
    candidate = _choose_base_variation(item)
    if candidate:
        changes.append(Change(item.id, item.name, f"Set BASE flag on existing variation (id={candidate.id})"))
        if not dry_run:
            candidate.is_base_unit = True
            candidate.active = True
            candidate.variation_qty = ONE
            candidate.save(update_fields=["is_base_unit", "active", "variation_qty"])
        return candidate

    # No variations at all — create base
    return _create_base_from_legacy(item, each, changes, dry_run)


def _create_base_from_legacy(
    item: InventoryMaster, each: Measurement, changes: List[Change], dry_run: bool
) -> InventoryQtyVariations:
    m = item.primary_base_unit if item.primary_base_unit_id else each
    changes.append(Change(item.id, item.name, f"Create BASE variation ({m.name}, 1.0000)"))
    if dry_run:
        # return a dummy-ish unsaved object for downstream logic (won't be used to save others)
        return InventoryQtyVariations(inventory=item, variation=m, variation_qty=ONE, is_base_unit=True, active=True)

    v = InventoryQtyVariations.objects.create(
        inventory=item,
        variation=m,
        variation_qty=ONE,
        is_base_unit=True,
        is_default_sell_uom=False,
        is_default_receive_uom=False,
        active=True,
    )
    return v


def _ensure_single_default(
    *,
    item: InventoryMaster,
    base: InventoryQtyVariations,
    field_name: str,
    changes: List[Change],
    dry_run: bool,
) -> None:
    """
    Ensure exactly one default flag (sell or receive) is set, and it's active.
    If none exists, set base as default.
    If multiple exist, keep best and unset others.
    """
    qs = item.variations.filter(**{field_name: True})

    # If base is unsaved dummy (dry-run create path), querysets still ok, but base.pk may be None.
    def _mark_default(v: InventoryQtyVariations) -> None:
        if getattr(v, field_name) is True and v.active:
            return
        changes.append(Change(item.id, item.name, f"Set {field_name}=True on id={v.id}"))
        if not dry_run:
            setattr(v, field_name, True)
            if not v.active:
                v.active = True
            v.save(update_fields=[field_name, "active"])

    def _unset_default(v: InventoryQtyVariations) -> None:
        changes.append(Change(item.id, item.name, f"Unset extra {field_name} on id={v.id}"))
        if not dry_run:
            setattr(v, field_name, False)
            v.save(update_fields=[field_name])

    if qs.count() == 0:
        # Set base as default
        if base.pk is not None:
            _mark_default(base)
        else:
            # base is dummy in dry-run; just log
            changes.append(Change(item.id, item.name, f"Would set {field_name}=True on BASE (new)"))
        return

    # If there is at least one, pick best: active first, base preferred, qty==1 preferred
    preferred = (
        qs.filter(active=True)
        .order_by(
            "-active",
            "-is_base_unit",
            "variation_qty",
            "id",
        )
        .first()
    )

    if preferred is None:
        # all inactive — promote base (or any)
        preferred = base if base.pk else qs.order_by("id").first()

    # Ensure preferred is active + default
    if preferred and preferred.pk is not None:
        if not preferred.active:
            changes.append(Change(item.id, item.name, f"Promote {field_name} id={preferred.id} to active=True"))
            if not dry_run:
                preferred.active = True
                preferred.save(update_fields=["active"])
        if not getattr(preferred, field_name):
            _mark_default(preferred)

    # Unset everyone else
    for other in qs.exclude(pk=getattr(preferred, "pk", None)):
        _unset_default(other)


class Command(BaseCommand):
    help = "Normalize Inventory UOM variations: ensure base + default sell/receive are consistent."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print changes only (default). No database writes.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes to the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of InventoryMaster items processed.",
        )
        parser.add_argument(
            "--item-id",
            type=int,
            default=None,
            help="Process a single InventoryMaster id.",
        )

    def handle(self, *args, **options):
        apply = bool(options["apply"])
        dry_run = not apply or bool(options["dry_run"])

        if apply and options["dry_run"]:
            self.stdout.write(self.style.WARNING("Both --apply and --dry-run provided; running DRY-RUN only."))
            dry_run = True

        each = _pick_each_measurement()

        qs = InventoryMaster.objects.all().order_by("id")
        if options["item_id"]:
            qs = qs.filter(pk=options["item_id"])
        if options["limit"]:
            qs = qs[: options["limit"]]

        changes: List[Change] = []
        processed = 0

        for item in qs.iterator():
            processed += 1
            # Work per item in its own transaction when applying
            ctx = transaction.atomic() if not dry_run else _noop_cm()
            with ctx:
                base = _ensure_base_variation(item, each, changes, dry_run)
                _ensure_single_default(
                    item=item,
                    base=base,
                    field_name="is_default_sell_uom",
                    changes=changes,
                    dry_run=dry_run,
                )
                _ensure_single_default(
                    item=item,
                    base=base,
                    field_name="is_default_receive_uom",
                    changes=changes,
                    dry_run=dry_run,
                )

        # Output
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN: no changes were written. Use --apply to persist.\n"))
        else:
            self.stdout.write(self.style.SUCCESS("APPLIED changes.\n"))

        self.stdout.write(f"Processed items: {processed}")
        self.stdout.write(f"Planned/Applied changes: {len(changes)}\n")

        # Print grouped by item
        last = None
        for c in changes:
            if c.item_id != last:
                self.stdout.write(self.style.MIGRATE_HEADING(f"\n#{c.item_id} — {c.item_name}"))
                last = c.item_id
            self.stdout.write(f"  - {c.action}")

        if not changes:
            self.stdout.write(self.style.SUCCESS("\nNo changes needed."))


class _noop_cm:
    def __enter__(self):  # noqa
        return self
    def __exit__(self, exc_type, exc, tb):  # noqa
        return False