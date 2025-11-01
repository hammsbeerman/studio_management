import re
from decimal import Decimal, InvalidOperation
from django.db import migrations, models

def to_decimal(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    # strip commas, currency symbols, stray text
    s = s.replace(",", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None

def copy_str_to_decimal(apps, schema_editor):
    Inventory = apps.get_model("inventory", "Inventory")
    for inv in Inventory.objects.all().only("pk", "unit_cost", "price_per_m"):
        uc = to_decimal(getattr(inv, "unit_cost", None))
        pm = to_decimal(getattr(inv, "price_per_m", None))
        updates = {}
        if uc is not None:
            updates["_unit_cost_dec"] = uc
        if pm is not None:
            updates["_price_per_m_dec"] = pm
        if updates:
            Inventory.objects.filter(pk=inv.pk).update(**updates)

def reverse_noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0075_keep_inventory_fk_nullable"),
    ]

    operations = [
        # 1) add temp decimal columns
        migrations.AddField(
            model_name="inventory",
            name="_unit_cost_dec",
            field=models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="inventory",
            name="_price_per_m_dec",
            field=models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True),
        ),

        # 2) copy/parse string values into decimals
        migrations.RunPython(copy_str_to_decimal, reverse_noop),

        # 3) drop old string columns
        migrations.RemoveField(model_name="inventory", name="unit_cost"),
        migrations.RemoveField(model_name="inventory", name="price_per_m"),

        # 4) rename temp decimals to final names
        migrations.RenameField(model_name="inventory", old_name="_unit_cost_dec",  new_name="unit_cost"),
        migrations.RenameField(model_name="inventory", old_name="_price_per_m_dec", new_name="price_per_m"),
    ]