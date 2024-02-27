# Generated by Django 4.2.9 on 2024-02-26 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0013_alter_workorder_original_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='added_to_parent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='parent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='parent_item',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Parent Item'),
        ),
    ]
