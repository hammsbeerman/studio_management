# Generated by Django 4.2.9 on 2024-09-04 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0051_rename_grouped_inventorymaster_not_grouped'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorymaster',
            name='not_grouped',
            field=models.BooleanField(default=False, verbose_name='Not Price Grouped'),
        ),
    ]