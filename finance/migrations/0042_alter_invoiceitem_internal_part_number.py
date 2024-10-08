# Generated by Django 4.2.9 on 2024-09-25 19:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0056_alter_vendor_options_and_more'),
        ('finance', '0041_allinvoiceitem_created_allinvoiceitem_updated_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='internal_part_number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_part_number', to='inventory.inventorymaster'),
        ),
    ]
