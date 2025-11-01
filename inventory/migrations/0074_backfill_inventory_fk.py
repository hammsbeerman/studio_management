from django.db import migrations, transaction
from django.utils.text import slugify  # optional

def forwards(apps, schema_editor):
    Inventory = apps.get_model('inventory', 'Inventory')
    InventoryMaster = apps.get_model('inventory', 'InventoryMaster')

    qs = Inventory.objects.filter(internal_part_number__isnull=True).only(
        "pk", "name", "description", "measurement", "retail_item"
    )

    with transaction.atomic():
        for inv in qs.iterator(chunk_size=500):
            master = InventoryMaster.objects.create(
                name=inv.name or f"Auto master for inv {inv.pk}",
                description=inv.description or "",
                primary_base_unit=getattr(inv, "measurement", None),
                retail=True if getattr(inv, "retail_item", None) else False,
                supplies=True,
                non_inventory=False,
                online_store=True,
            )
            inv.internal_part_number_id = master.pk
            inv.save(update_fields=["internal_part_number"])

def backwards(apps, schema_editor):
    # No-op
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0072_orderout_checks"),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]