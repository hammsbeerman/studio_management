# Generated by Django 4.2.9 on 2024-08-24 20:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0036_vendoritemdetail'),
        ('finance', '0019_alter_accountspayable_amount'),
        ('retail', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ItemInvoice',
            new_name='InvoiceItem',
        ),
    ]
