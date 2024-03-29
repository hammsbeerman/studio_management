# Generated by Django 4.2.9 on 2024-03-01 22:01

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pricesheet', '0007_wideformatpricesheet_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='wideformatpricesheet',
            name='dateentered',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wideformatpricesheet',
            name='edited',
            field=models.BooleanField(default=False, verbose_name='Edited'),
        ),
    ]
