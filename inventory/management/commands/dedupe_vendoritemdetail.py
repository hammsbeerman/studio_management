from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Max, Q
from django.apps import apps


class Command(BaseCommand):
    help = (
        "Deduplicate VendorItemDetail rows that share the same "
        "(internal_part_number, vendor). Keeps one row per key and deletes others."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without writing to the database.",
        )
        parser.add_argument(
            "--keep",
            choices=["latest", "earliest"],
            default="latest",
            help="Which row to keep within each duplicate group (default: latest).",
        )
        parser.add_argument(
            "--vendor-id",
            type=int,
            action="append",
            dest="vendor_ids",
            help="Limit to one or more vendor IDs (can be passed multiple times).",
        )
        parser.add_argument(
            "--ipn-id",
            type=int,
            action="append",
            dest="ipn_ids",
            help="Limit to one or more InventoryMaster IDs (can be passed multiple times).",
        )
        parser.add_argument(
            "--no-merge-high",
            action="store_true",
            help="Do not merge the maximum high_price into the kept row.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Only process this many duplicate groups (useful for testing).",
        )

    def handle(self, *args, **options):
        VendorItemDetail = apps.get_model("inventory", "VendorItemDetail")

        # Build the duplicate groups query
        dupes = (
            VendorItemDetail.objects.values("internal_part_number_id", "vendor_id")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
        )

        # Optional filters
        vendor_ids = options.get("vendor_ids")
        ipn_ids = options.get("ipn_ids")
        if vendor_ids:
            dupes = dupes.filter(vendor_id__in=vendor_ids)
        if ipn_ids:
            dupes = dupes.filter(internal_part_number_id__in=ipn_ids)

        # Optional limiting
        limit = options.get("limit")
        if limit:
            dupes = dupes[:limit]

        dry_run = options["dry_run"]
        keep_strategy = options["keep"]
        merge_high = not options["no_merge_high"]

        total_groups = dupes.count()
        if total_groups == 0:
            self.stdout.write(self.style.SUCCESS("No duplicate groups found."))
            return

        self.stdout.write(
            f"Found {total_groups} duplicate key group(s){' (dry-run)' if dry_run else ''}."
        )

        groups_processed = 0
        rows_deleted_total = 0

        # Order to pick the "keep" row
        if keep_strategy == "latest":
            ordering = ["-updated", "-id"]
        else:  # "earliest"
            ordering = ["updated", "id"]

        # Use a transaction so each group fix is atomic.
        # Still safe in dry-run (no writes occur).
        with transaction.atomic():
            for key in dupes:
                ipn_id = key["internal_part_number_id"]
                vendor_id = key["vendor_id"]

                group_qs = (
                    VendorItemDetail.objects.filter(
                        internal_part_number_id=ipn_id, vendor_id=vendor_id
                    )
                    .order_by(*ordering)
                )

                count = group_qs.count()
                keep = group_qs.first()
                to_delete = group_qs.exclude(pk=keep.pk)

                # Merge: best high_price
                if merge_high:
                    best_high = group_qs.aggregate(Max("high_price"))["high_price__max"]
                    if best_high is not None and (keep.high_price or 0) != best_high:
                        self.stdout.write(
                            f"Group (ipn={ipn_id}, vendor={vendor_id}): "
                            f"setting kept row id={keep.id} high_price -> {best_high}"
                        )
                        if not dry_run:
                            keep.high_price = best_high
                            keep.save(update_fields=["high_price"])

                # Report what we’re keeping/deleting
                self.stdout.write(
                    f"Group (ipn={ipn_id}, vendor={vendor_id}): {count} rows -> keep id={keep.id}, delete {to_delete.count()} row(s)"
                )

                # Perform deletion (unless dry-run)
                if not dry_run and to_delete.exists():
                    deleted_count, _ = to_delete.delete()
                    rows_deleted_total += deleted_count

                groups_processed += 1

            if dry_run:
                # Roll back any accidental writes in dry-run (should be none).
                transaction.set_rollback(True)

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] Would process {groups_processed} group(s); "
                    f"would delete ~{rows_deleted_total} row(s)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed {groups_processed} group(s); deleted {rows_deleted_total} duplicate row(s)."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "You can now re-run your migration that adds the unique constraint."
                )
            )

#python manage.py dedupe_vendoritemdetail --dry-run

#python manage.py dedupe_vendoritemdetail