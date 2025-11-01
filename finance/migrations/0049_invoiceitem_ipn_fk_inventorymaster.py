from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        # make sure we run after the migration that ADDS InventoryMaster.internal_part_number
        ("inventory", "0086_inventoryitem_inventorymergelog_pricehistory_and_more"),   # <-- adjust if your file is named differently
        ("finance", "0048_alter_invoiceitem_internal_part_number"),  # last finance migration you ran
    ]

    operations = [
        migrations.AlterField(
            model_name="invoiceitem",
            name="internal_part_number",
            field=models.ForeignKey(
                to="inventory.inventorymaster",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invoice_items",
                related_query_name="invoice_item",
            ),
        ),
    ]