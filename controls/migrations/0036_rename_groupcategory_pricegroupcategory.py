# Generated by Django 4.2.9 on 2024-09-06 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0056_alter_inventorymaster_price_group'),
        ('controls', '0035_alter_groupcategory_name'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GroupCategory',
            new_name='PriceGroupCategory',
        ),
    ]
