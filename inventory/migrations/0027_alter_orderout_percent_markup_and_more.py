# Generated by Django 4.2.9 on 2024-04-15 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0026_alter_setprice_side_2_inktype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderout',
            name='percent_markup',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Percent Markup'),
        ),
        migrations.AlterField(
            model_name='orderout',
            name='purchase_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Purchase Price'),
        ),
        migrations.AlterField(
            model_name='orderout',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Quantity'),
        ),
    ]
