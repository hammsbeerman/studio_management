# Generated by Django 4.2.9 on 2024-03-03 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0017_inventory_length_measurement_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='type_mask',
            field=models.BooleanField(default=False, verbose_name='Mask'),
        ),
    ]
