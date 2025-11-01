from django.db import migrations, models, connection

def copy_m2m_to_through(apps, schema_editor):
    InventoryPricingGroup = apps.get_model("inventory", "InventoryPricingGroup")
    InventoryMaster = apps.get_model("inventory", "InventoryMaster")
    GroupCategory = apps.get_model("controls", "GroupCategory")

    # The old auto M2M table name (adjust if your DB uses a different name):
    # Typically: <app>_<model>_<field>
    table = "inventory_inventorymaster_price_group"

    with connection.cursor() as cursor:
        # columns typically: inventorymaster_id, groupcategory_id
        cursor.execute(f"SELECT inventorymaster_id, groupcategory_id FROM {table}")
        rows = cursor.fetchall()

    # Insert into explicit through, ignore duplicates
    for inv_id, grp_id in rows:
        InventoryPricingGroup.objects.get_or_create(
            inventory_id=inv_id, group_id=grp_id
        )

class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0077_merge_20250923_1541"),  # or your current head
    ]
    operations = [
        # No need to AddField for price_groups2 if you already added it to the model
        migrations.RunPython(copy_m2m_to_through, migrations.RunPython.noop),
    ]