# Generated by Django 4.2.9 on 2024-02-07 23:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_inventory_price_per_m'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventory',
            name='category',
        ),
    ]
