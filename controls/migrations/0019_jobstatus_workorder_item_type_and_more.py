# Generated by Django 4.2.9 on 2024-03-12 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0018_paymenttype_detail_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobstatus',
            name='workorder_item_type',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Workorder Item Type'),
        ),
        migrations.AddField(
            model_name='jobstatus',
            name='workorder_type',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Workorder Type'),
        ),
    ]
