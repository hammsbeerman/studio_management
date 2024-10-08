# Generated by Django 4.2.9 on 2024-08-25 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0040_inventorymaster_measurement_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorymaster',
            name='price_per_sqft',
        ),
        migrations.AlterField(
            model_name='inventorymaster',
            name='high_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True, verbose_name='High Price'),
        ),
        migrations.AlterField(
            model_name='inventorymaster',
            name='price_per_m',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True, verbose_name='Price Per M'),
        ),
        migrations.AlterField(
            model_name='inventorymaster',
            name='unit_cost',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True, verbose_name='Unit Cost'),
        ),
    ]
