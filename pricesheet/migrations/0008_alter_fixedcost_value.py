# Generated by Django 4.2.9 on 2024-02-05 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricesheet', '0007_rename_fixedcosts_fixedcost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fixedcost',
            name='value',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Value'),
        ),
    ]