from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_old_to_new_through(apps, schema_editor):
    """
    Copies links from either:
      - OLD FK 'price_group' on InventoryMaster (if it still exists in DB), or
      - TEMP auto-through M2M 'price_groups_temp' (if it exists),
    into the final through table 'inventory.InventoryPricingGroup'.
    """
    InventoryMaster = apps.get_model('inventory', 'InventoryMaster')
    InventoryPricingGroup = apps.get_model('inventory', 'InventoryPricingGroup')

    # Copy from temp M2M (if present)
    ThroughTemp = None
    try:
        ThroughTemp = InventoryMaster._meta.get_field('price_groups_temp').remote_field.through
    except Exception:
        ThroughTemp = None

    if ThroughTemp:
        for row in ThroughTemp.objects.all():
            # Left side (InventoryMaster FK) — Django may name it differently
            item_id = getattr(row, 'inventorymaster_id', None) or getattr(row, 'inventory_master_id', None)
            # Right side (GroupCategory FK)
            group_id = getattr(row, 'groupcategory_id', None) or getattr(row, 'pricegroup_id', None)
            if item_id and group_id:
                InventoryPricingGroup.objects.get_or_create(
                    inventory_id=item_id,
                    group_id=group_id,
                )

    # Copy from old FK price_group (if FK column still exists)
    try:
        for im in InventoryMaster.objects.all():
            gid = getattr(im, 'price_group_id', None)
            if gid:
                InventoryPricingGroup.objects.get_or_create(
                    inventory_id=im.id,
                    group_id=gid,
                )
    except Exception:
        # FK already gone — nothing to do
        pass

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('controls', '0041_alter_setpricecategory_options_and_more'),
        ('inventory', '0085_alter_orderout_options_and_more'),
    ]

    operations = [
        # 1) ADD a new M2M name to avoid ALTER
        migrations.AddField(
            model_name='inventorymaster',
            name='price_group_new',
            field=models.ManyToManyField(
                to='controls.groupcategory',
                through='inventory.InventoryPricingGroup',
                through_fields=('inventory', 'group'),
                related_name='items',
                blank=True,
            ),
        ),

        # 2) COPY any existing links (from FK or temp M2M) into the through table
        migrations.RunPython(copy_old_to_new_through, migrations.RunPython.noop),

        # 3) DROP the OLD FK 'price_group' (this exists in 0085 schema)
        migrations.RemoveField(
            model_name='inventorymaster',
            name='price_group',
        ),

        # NOTE: If you ALSO have a temp auto-through field 'price_groups_temp' in your DB,
        # create a tiny follow-up migration to RemoveField(name='price_groups_temp').

        # 4) RENAME the new field to the canonical name
        migrations.RenameField(
            model_name='inventorymaster',
            old_name='price_group_new',
            new_name='price_group',
        ),
    ]