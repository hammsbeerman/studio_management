# Generated by Django 4.2.9 on 2024-08-07 18:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0012_retailinvoiceitem_vendor'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RetailItemDetail',
            new_name='RetailVendorItemDetail',
        ),
    ]
