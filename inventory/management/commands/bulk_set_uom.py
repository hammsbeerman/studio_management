from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from inventory.models import Measurement
from inventory.services.uom_bulk import build_item_queryset, bulk_set_item_uom


class Command(BaseCommand):
    help = "Bulk create/set InventoryQtyVariations and optionally set base/default UOM flags."

    def add_arguments(self, parser):
        parser.add_argument("--measurement-id", type=int, required=True)
        parser.add_argument("--variation-qty", type=str, default="1.0000")
        parser.add_argument("--name-contains", type=str, default="")
        parser.add_argument("--vendor-id", type=int, default=None)

        parser.add_argument("--set-base", action="store_true")
        parser.add_argument("--set-default-sell", action="store_true")
        parser.add_argument("--set-default-receive", action="store_true")

        parser.add_argument("--apply", action="store_true")  # otherwise dry-run

    def handle(self, *args, **opts):
        m = Measurement.objects.filter(pk=opts["measurement_id"]).first()
        if not m:
            raise CommandError("Measurement not found")

        variation_qty = Decimal(opts["variation_qty"])

        qs = build_item_queryset(
            only_active=True,
            name_contains=opts["name_contains"],
            vendor_id=opts["vendor_id"],
        )

        res = bulk_set_item_uom(
            item_qs=qs,
            measurement=m,
            variation_qty=variation_qty,
            set_as_base=opts["set_base"],
            set_as_default_sell=opts["set_default_sell"],
            set_as_default_receive=opts["set_default_receive"],
            dry_run=not opts["apply"],
        )

        self.stdout.write(self.style.SUCCESS(
            f"matched={res.matched} changed={res.changed} created={res.created} skipped={res.skipped} "
            f"(dry_run={not opts['apply']})"
        ))