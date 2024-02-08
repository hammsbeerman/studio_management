# Generated by Django 4.2.9 on 2024-02-07 17:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_inventory_price_per_m'),
        ('pricesheet', '0011_pricesheet_side_1_inktype_pricesheet_side_2_inktype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pricesheet',
            name='paper_stock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='inventory.inventory'),
        ),
    ]
