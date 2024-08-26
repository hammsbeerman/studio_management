# Generated by Django 4.2.9 on 2024-08-19 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0017_alter_accountspayable_invoice_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountspayable',
            name='retail_invoice',
            field=models.BooleanField(default=True, null=True, verbose_name='Retail Invoice'),
        ),
        migrations.AddField(
            model_name='accountspayable',
            name='supplies_invoice',
            field=models.BooleanField(default=True, null=True, verbose_name='Supplies Invoice'),
        ),
        migrations.AddField(
            model_name='accountspayable',
            name='total',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Total'),
        ),
    ]