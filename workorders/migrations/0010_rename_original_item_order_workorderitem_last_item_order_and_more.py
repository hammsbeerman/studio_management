# Generated by Django 4.2.9 on 2024-01-18 22:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0009_workorderitem_internal_company_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workorderitem',
            old_name='original_item_order',
            new_name='last_item_order',
        ),
        migrations.RenameField(
            model_name='workorderitem',
            old_name='original_item_price',
            new_name='last_item_price',
        ),
    ]
