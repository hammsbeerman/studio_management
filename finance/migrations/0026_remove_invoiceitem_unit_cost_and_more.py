# Generated by Django 4.2.9 on 2024-08-26 21:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0045_inventoryqtyvariations_variation_qty'),
        ('finance', '0025_remove_invoiceitem_variation_qty_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoiceitem',
            name='unit_cost',
        ),
        migrations.RemoveField(
            model_name='invoiceitem',
            name='variation',
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='invoice_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.inventoryqtyvariations'),
        ),
    ]
