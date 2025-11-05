#######Not used yet
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, Q
from inventory.models import InventoryMaster, InventoryMerge

# Choose your dedupe key(s). Common options:
#   - internal_part_number (your “SKU”)
#   - vendor + vendor_part_number
#   - normalized name + dimensions
DEDUP_KEYS = ["internal_part_number"]  # adjust to your schema

# Models to re-point (non-history) — only if you want future relations moved.
# Keep invoice history untouched by not listing finance models here.
REPOINTS = [
    # ("inventory", "VendorItemDetail", "inventory_master"),
    # ("inventory", "InventoryDetail", "item"),
    # add tuples of (app_label, model_name, fk_field_name) if you need
]

class Command(BaseCommand):
    help = "Merge duplicate InventoryMaster records by key. Marks dupes inactive, keeps history. Creates InventoryMerge rows."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Plan only, no writes.")
        parser.add_argument("--by", choices=["sku", "vendor_part", "name"], default="sku",
                            help="Strategy for grouping duplicates.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        strategy = opts["by"]

        if strategy == "sku":
            keyfn = self.key_by_sku
        elif strategy == "vendor_part":
            keyfn = self.key_by_vendor_part
        else:
            keyfn = self.key_by_name

        groups = defaultdict(list)
        qs = InventoryMaster.objects.all().order_by("id")
        for obj in qs:
            k = keyfn(obj)
            if k:
                groups[k].append(obj)

        dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
        if not dup_groups:
            self.stdout.write(self.style.SUCCESS("No duplicates found by strategy: %s" % strategy))
            return

        self.stdout.write(f"Found {len(dup_groups)} duplicate groups.")

        with transaction.atomic():
            for k, objs in dup_groups.items():
                # Pick canonical: highest usage or lowest id
                canonical = self.pick_canonical(objs)
                others = [o for o in objs if o.id != canonical.id]

                self.stdout.write(f"\nKey={k} -> canonical #{canonical.id} ({canonical}) ; dupes={ [o.id for o in others] }")

                # Create merge links + deactivate dupes
                for dupe in others:
                    # Create link if not exists
                    InventoryMerge.objects.get_or_create(from_item=dupe, to_item=canonical, defaults={"reason": strategy})
                    # Deactivate dupe
                    if dupe.active:
                        dupe.active = False
                        if not dry:
                            dupe.save(update_fields=["active"])

                # Optionally re-point non-history relations to canonical for future
                if REPOINTS:
                    for app, model_name, fk in REPOINTS:
                        Model = self.get_model(app, model_name)
                        if not Model:
                            continue
                        for dupe in others:
                            q = {fk: dupe}
                            if not dry:
                                Model.objects.filter(**q).update(**{fk: canonical})

            if dry:
                self.stdout.write(self.style.WARNING("Dry-run complete. No changes committed."))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("Merges committed."))

    # --- strategies ---
    def key_by_sku(self, obj):
        sku = getattr(obj, "internal_part_number", "") or getattr(obj, "sku", "")
        return sku.strip().lower() if sku else None

    def key_by_vendor_part(self, obj):
        vendor = getattr(obj, "vendor", None)
        vendor_id = getattr(vendor, "id", None)
        part = getattr(obj, "vendor_part_number", "")
        if vendor_id and part:
            return f"v{vendor_id}:{part.strip().lower()}"
        return None

    def key_by_name(self, obj):
        name = getattr(obj, "name", "")
        return name.strip().lower() if name else None

    # --- helpers ---
    def pick_canonical(self, objs):
        # Prefer active; then with most references; fallback to lowest id
        actives = [o for o in objs if getattr(o, "active", True)]
        pool = actives or objs
        # If you track usage counts, implement here; else lowest id:
        return sorted(pool, key=lambda o: o.id)[0]

    def get_model(self, app_label, model_name):
        from django.apps import apps
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            self.stdout.write(self.style.WARNING(f"Missing model {app_label}.{model_name}"))
            return None