# Generated by Django 4.2.9 on 2024-08-24 20:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0003_delete_testtable_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InvoiceItem',
        ),
    ]