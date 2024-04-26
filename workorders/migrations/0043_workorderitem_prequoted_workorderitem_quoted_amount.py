# Generated by Django 4.2.9 on 2024-04-24 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0042_remove_workorder_disount_applied'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='prequoted',
            field=models.BooleanField(default=False, verbose_name='Prequoted'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='quoted_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Quoted Amount'),
        ),
    ]