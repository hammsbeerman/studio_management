# Generated by Django 4.2.9 on 2024-01-22 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0010_rename_original_item_order_workorderitem_last_item_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='workorder_hr',
            field=models.CharField(default='1', max_length=100, verbose_name='Workorder'),
            preserve_default=False,
        ),
    ]
