# Generated by Django 4.2.9 on 2024-08-19 21:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0033_vendor_retail_vendor'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InventoryMaster',
        ),
    ]
