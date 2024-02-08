# Generated by Django 4.2.9 on 2024-02-07 23:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_remove_inventory_category'),
        ('workorders', '0030_category_customform_alter_subcategory_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='percent_markup',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Percent Markup'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='purchase_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Purchase Price'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='vendor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='inventory.vendor'),
        ),
    ]
