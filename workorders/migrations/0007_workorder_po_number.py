# Generated by Django 4.2.9 on 2024-01-17 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0006_workorder_lk_workorder_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='po_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='PO Number'),
        ),
    ]
