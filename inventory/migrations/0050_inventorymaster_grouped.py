# Generated by Django 4.2.9 on 2024-09-04 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0049_alter_inventoryqtyvariations_variation_qty'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorymaster',
            name='grouped',
            field=models.BooleanField(default=True, verbose_name='Not Price Grouped'),
        ),
    ]