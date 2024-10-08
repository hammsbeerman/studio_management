# Generated by Django 4.2.9 on 2024-09-11 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0036_alter_invoiceitem_unit_cost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='invoice_unit_cost',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=15, null=True, verbose_name='Invoice Unit Cost'),
        ),
    ]
