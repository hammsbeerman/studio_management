from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


def _remap_logs_to_master(apps, schema_editor):
    """
    Best-effort: if any InventoryMergeLog rows were created while `target`
    pointed to the accidental InventoryItem model, try to remap them to
    InventoryMaster. If details contains 'target_master_id', prefer that.
    """
    Log = apps.get_model("inventory", "InventoryMergeLog")
    Master = apps.get_model("inventory", "InventoryMaster")

    for log in Log.objects.all():
        target_id = None
        details = log.details or {}
        if isinstance(details, dict):
            target_id = details.get("target_master_id")

        if target_id is not None:
            try:
                log.target = Master.objects.get(pk=target_id)
                log.save(update_fields=["target"])
            except Master.DoesNotExist:
                # Leave as-is if we can't resolve it.
                pass


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0088_inventoryitem_inventorymergelog_pricehistory_and_more"),
    ]

    operations = [
        # Remove the accidental models/tables introduced in 0088 (safe if they don't exist)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DROP TABLE IF EXISTS "inventory_vendoritem";
                        DROP TABLE IF EXISTS "inventory_pricehistory";
                        DROP TABLE IF EXISTS "inventory_purchaseline";
                        DROP TABLE IF EXISTS "inventory_workorderitem";
                        DROP TABLE IF EXISTS "inventory_inventoryitem";
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name="VendorItem"),
                migrations.DeleteModel(name="PriceHistory"),
                migrations.DeleteModel(name="PurchaseLine"),
                migrations.DeleteModel(name="WorkorderItem"),
                migrations.DeleteModel(name="InventoryItem"),
            ],
        ),

        # Point InventoryMergeLog.target back to InventoryMaster
        migrations.AlterField(
            model_name="inventorymergelog",
            name="target",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="inventory.inventorymaster",
            ),
        ),

        # Best-effort data shim for logs
        migrations.RunPython(_remap_logs_to_master, migrations.RunPython.noop),

        # Keep your change to OrderOut.open default
        migrations.AlterField(
            model_name="orderout",
            name="open",
            field=models.BooleanField(default=False),
        ),

        # Add the "not both open and billed" DB constraint (fixes the failing test)
        migrations.AddConstraint(
            model_name="orderout",
            constraint=models.CheckConstraint(
                name="oo_not_both_open_and_billed",
                check=~(Q(open=True) & Q(billed=True)),
            ),
        ),
    ]