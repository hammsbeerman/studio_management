# Generated by Django 4.2.9 on 2024-01-30 02:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pricesheet', '0002_pricesheet_edited'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pricesheet',
            name='edited',
        ),
    ]