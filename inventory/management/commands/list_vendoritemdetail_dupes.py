# inventory/management/commands/list_vendoritemdetail_dupes.py
import csv
from typing import List, Dict, Any
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.apps import apps


class Command(BaseCommand):
    help = (
        "List duplicate VendorItemDetail rows that share the same "
        "(internal_part_number, vendor). Does NOT modify the database."
    )

    def add_arguments(self, parser):
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
            "--limit",
            type=int,
            help="Only process this many duplicate groups (useful for testing).",
        )
        parser.add_argument(
            "--details",
            action="store_true",
            help="Show per-row details for each duplicate group.",
        )
        parser.add_argument(
            "--csv",
            action="store_true",
            help="Output CSV to stdout instead of human-readable text.",
        )
        parser.add_argument(
            "--outfile",
            type=str,
            help="Write CSV to the specified file path.",
        )

    def handle(self, *args, **options):
        VendorItemDetail = apps.get_model("inventory", "VendorItemDetail")
        Vendor = apps.get_model("inventory", "Vendor")
        InventoryMaster = apps.get_model("inventory", "InventoryMaster")

        # Build duplicate key groups
        dupes = (
            VendorItemDetail.objects.values("internal_part_number_id", "vendor_id")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("-cnt", "vendor_id", "internal_part_number_id")
        )

        # Optional filters
        vendor_ids = options.get("vendor_ids")
        ipn_ids = options.get("ipn_ids")
        if vendor_ids:
            dupes = dupes.filter(vendor_id__in=vendor_ids)
        if ipn_ids:
            dupes = dupes.filter(internal_part_number_id__in=ipn_ids)

        limit = options.get("limit")
        if limit:
            dupes = dupes[:limit]

        dupes = list(dupes)
        if not dupes:
            self.stdout.write(self.style.SUCCESS("No duplicate groups found."))
            return

        # Build name maps to avoid N+1 lookups
        vendor_id_set = {d["vendor_id"] for d in dupes}
        ipn_id_set = {d["internal_part_number_id"] for d in dupes}

        vendor_map: Dict[int, str] = {
            v["id"]: v["name"]
            for v in Vendor.objects.filter(id__in=vendor_id_set).values("id", "name")
        }
        ipn_map: Dict[int, str] = {
            i["id"]: i["name"]
            for i in InventoryMaster.objects.filter(id__in=ipn_id_set).values("id", "name")
        }

        details = options["details"]
        to_csv = options["csv"]
        outfile = options.get("outfile")

        # If both CSV to stdout and outfile specified, prefer outfile.
        writer = None
        file_handle = None
        if to_csv or outfile:
            fieldnames = [
                "internal_part_number_id",
                "internal_part_number_name",
                "vendor_id",
                "vendor_name",
                "duplicate_count",
                "duplicate_ids",
            ]
            if outfile:
                file_handle = open(outfile, "w", newline="", encoding="utf-8")
                writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            else:
                writer = csv.DictWriter(self.stdout, fieldnames=fieldnames)
            writer.writeheader()

        total_groups = len(dupes)
        self.stdout.write(f"Found {total_groups} duplicate group(s).")

        for group in dupes:
            ipn_id = group["internal_part_number_id"]
            vendor_id = group["vendor_id"]
            count = group["cnt"]
            ipn_name = ipn_map.get(ipn_id, f"(id:{ipn_id})")
            vendor_name = vendor_map.get(vendor_id, f"(id:{vendor_id})")

            group_qs = VendorItemDetail.objects.filter(
                internal_part_number_id=ipn_id, vendor_id=vendor_id
            ).order_by("-updated", "-id")

            ids: List[int] = list(group_qs.values_list("id", flat=True))

            if writer:
                writer.writerow(
                    {
                        "internal_part_number_id": ipn_id,
                        "internal_part_number_name": ipn_name,
                        "vendor_id": vendor_id,
                        "vendor_name": vendor_name,
                        "duplicate_count": count,
                        "duplicate_ids": " ".join(map(str, ids)),
                    }
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n(ipn={ipn_id} “{ipn_name}”, vendor={vendor_id} “{vendor_name}”) "
                        f"→ {count} rows: {ids}"
                    )
                )

            if details and not writer:
                for row in group_qs:
                    self.stdout.write(
                        f"  - id={row.id}  updated={row.updated}  created={row.created}  "
                        f"vendor_part_number={row.vendor_part_number!r}  "
                        f"high_price={row.high_price}"
                    )

        if file_handle:
            file_handle.close()
            self.stdout.write(self.style.SUCCESS(f"\nCSV written to: {outfile}"))

        self.stdout.write(self.style.SUCCESS("\nDone. (No data was modified.)"))

#python manage.py list_vendoritemdetail_dupes
#python manage.py list_vendoritemdetail_dupes --details