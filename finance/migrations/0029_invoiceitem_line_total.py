# Generated by Django 4.2.9 on 2024-08-26 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0028_remove_invoiceitem_price_ea_invoiceitem_unit_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='line_total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Line Total'),
        ),
    ]
