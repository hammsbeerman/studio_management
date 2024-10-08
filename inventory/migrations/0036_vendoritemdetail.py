# Generated by Django 4.2.9 on 2024-08-24 19:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0035_inventorymaster'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorItemDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('vendor_part_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Vendor Part Number')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('supplies', models.BooleanField(default=True, verbose_name='Supply Item')),
                ('retail', models.BooleanField(default=True, verbose_name='Retail Item')),
                ('non_inventory', models.BooleanField(default=False, verbose_name='Non Inventory Item')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('high_price', models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True, verbose_name='High Price')),
                ('internal_part_number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.inventorymaster')),
                ('vendor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.vendor')),
            ],
        ),
    ]
