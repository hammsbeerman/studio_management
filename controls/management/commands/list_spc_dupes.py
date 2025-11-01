from django.core.management.base import BaseCommand
from django.db.models import Count
from controls.models import SetPriceCategory

class Command(BaseCommand):
    help = "List duplicate SetPriceCategory rows (same (category, name))."

    def handle(self, *args, **options):
        dupes = (
            SetPriceCategory.objects
            .values('category_id', 'name')
            .annotate(n=Count('id'))
            .filter(n__gt=1)
        )
        if not dupes.exists():
            self.stdout.write(self.style.SUCCESS("No duplicates found."))
            return

        for g in dupes:
            rows = (
                SetPriceCategory.objects
                .filter(category_id=g['category_id'], name=g['name'])
                .select_related('category')
                .order_by('id')
                .values('id', 'category_id', 'category__name', 'name', 'created', 'updated')
            )
            header = f"(category_id={g['category_id']}, category='{rows[0]['category__name']}', name='{g['name']}') -> {len(rows)} rows"
            self.stdout.write(self.style.WARNING("\n" + header))
            for r in rows:
                self.stdout.write(f"  {r}")

#python manage.py list_spc_dupes