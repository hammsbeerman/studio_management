from typing import Dict, Iterable
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from controls.models import JobStatus, Numbering, Measurement

JOB_STATUSES: Iterable[str] = (
    "Open",
    "Quoted",
    "In Progress",
    "Waiting on Customer",
    "Waiting on Vendor",
    "Order Out",
    "Ready for Pickup",
    "Completed",
    "Billed",
    "Void",
)

# Prefer stable IDs so legacy code that used pk=1/2 keeps working.
NUMBERING_SEEDS = [
    {"id": 1, "name": "Workorder Number", "prefix": "WO", "padding": 5, "start": 1},
    {"id": 2, "name": "Customer Number",  "prefix": "C",  "padding": 5, "start": 1},
    {"id": 3, "name": "Quote Number",     "prefix": "Q",  "padding": 5, "start": 1},
]

# Add/trim as you like; this tolerates models that only have `name`.
MEASUREMENTS = [
    {"name": "Each",   "abbr": "ea",  "type": "count"},
    {"name": "Sheet",  "abbr": "sht", "type": "count"},
    {"name": "Pack",   "abbr": "pk",  "type": "count"},
    {"name": "Box",    "abbr": "box", "type": "count"},
    {"name": "Inch",   "abbr": "in",  "type": "length"},
    {"name": "Foot",   "abbr": "ft",  "type": "length"},
    {"name": "Yard",   "abbr": "yd",  "type": "length"},
    {"name": "Millimeter", "abbr": "mm", "type": "length"},
    {"name": "Centimeter", "abbr": "cm", "type": "length"},
    {"name": "Meter",  "abbr": "m",   "type": "length"},
    {"name": "Square Foot", "abbr": "sqft", "type": "area"},
    {"name": "Square Meter","abbr": "sqm",  "type": "area"},
]

def _field_set(Model):
    return {
        f.name for f in Model._meta.get_fields()
        if getattr(f, "concrete", False) and not getattr(f, "auto_created", False)
    }

class Command(BaseCommand):
    help = "First-run bootstrap: seeds JobStatus, Numbering, and Measurement (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Plan only, no writes.")
        parser.add_argument("--quiet", action="store_true", help="Minimal output.")

    def _log(self, quiet: bool, msg: str):
        if not quiet:
            self.stdout.write(msg)

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        quiet = opts["quiet"]

        # 1) JobStatus
        created_js = 0
        for name in JOB_STATUSES:
            obj, made = JobStatus.objects.get_or_create(name=name, defaults={"icon": ""})
            created_js += int(made)
        self._log(quiet, f"JobStatus: ensured {len(JOB_STATUSES)} rows (created {created_js}).")

        # 2) Numbering (schema-aware: supports value OR current; optional name/prefix/padding)
        nf = _field_set(Numbering)
        counter_field = "value" if "value" in nf else ("current" if "current" in nf else None)

        created_num = 0
        for seed in NUMBERING_SEEDS:
            kwargs = {}
            if "id" in nf:      kwargs["id"] = seed["id"]
            if "name" in nf:    kwargs["name"] = seed["name"]

            defaults: Dict = {}
            if "name" in nf:    defaults.setdefault("name", seed["name"])
            if "prefix" in nf:  defaults["prefix"] = seed["prefix"]
            if "padding" in nf: defaults["padding"] = seed["padding"]
            if counter_field:   defaults[counter_field] = seed["start"]

            obj, made = Numbering.objects.get_or_create(defaults=defaults, **kwargs)
            created_num += int(made)

            # If it existed but counter is missing, initialize it
            if counter_field and getattr(obj, counter_field, None) in (None, ""):
                Numbering.objects.filter(pk=obj.pk).update(**{counter_field: seed["start"]})

        self._log(quiet, f"Numbering: ensured {len(NUMBERING_SEEDS)} rows (created {created_num}).")

        # 3) Measurements (schema-aware for optional fields)
        mf = _field_set(Measurement)
        created_meas = 0
        for m in MEASUREMENTS:
            kwargs = {"name": m["name"]}
            defaults = {}
            if "abbr" in mf:      defaults["abbr"] = m["abbr"]
            if "code" in mf:      defaults["code"] = m["abbr"]  # if you have a code field
            if "unit_type" in mf: defaults["unit_type"] = m["type"]
            if "type" in mf:      defaults["type"] = m["type"]  # some schemas use 'type'

            obj, made = Measurement.objects.get_or_create(defaults=defaults, **kwargs)
            created_meas += int(made)

        self._log(quiet, f"Measurement: ensured {len(MEASUREMENTS)} rows (created {created_meas}).")

        if dry:
            self._log(quiet, "Dry-run: rolling back.")
            transaction.set_rollback(True)
        else:
            self._log(quiet, self.style.SUCCESS("First-run bootstrap complete."))