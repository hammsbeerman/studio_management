# Generated by Django 4.2.9 on 2024-09-03 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0048_remove_inventorymaster_units_per_package_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryqtyvariations',
            name='variation_qty',
            field=models.DecimalField(decimal_places=4, default=1, max_digits=15, verbose_name='Variation Qty'),
            preserve_default=False,
        ),
    ]
