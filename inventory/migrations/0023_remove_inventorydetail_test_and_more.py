# Generated by Django 4.2.9 on 2024-04-02 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0022_alter_orderout_workorder_alter_photography_workorder_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorydetail',
            name='test',
        ),
        migrations.AddField(
            model_name='inventorydetail',
            name='invoice_date',
            field=models.DateField(blank=True, null=True, verbose_name='Invoice Date'),
        ),
        migrations.AddField(
            model_name='inventorydetail',
            name='price_per_m',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Paper Stock Price per M'),
        ),
    ]
