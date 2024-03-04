# Generated by Django 4.2.9 on 2024-03-03 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0015_inventory_height_inventory_width'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventory',
            name='height',
        ),
        migrations.AddField(
            model_name='inventory',
            name='length',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Length'),
        ),
    ]
