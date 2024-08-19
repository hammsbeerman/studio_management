# Generated by Django 4.2.9 on 2024-06-06 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceBreaks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Name')),
                ('qty_full_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Full Price Qty')),
                ('full_price_pct', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Full Price Pct')),
                ('qty_break_one', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Break 1 Qty')),
                ('break_one_pct', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Break 1 Pct')),
                ('qty_break_two', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Break 2 Qty')),
                ('break_two_pct', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Break 2 Pct')),
            ],
        ),
    ]