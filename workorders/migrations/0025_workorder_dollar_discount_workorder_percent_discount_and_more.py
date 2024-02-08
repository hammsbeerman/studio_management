# Generated by Django 4.2.9 on 2024-02-05 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0024_workorder_tax_exempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='dollar_discount',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Discount $'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='percent_discount',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Discount %'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='subtotal',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Subtotal'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='tax',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Tax'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='workorder_total',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Workorder Total'),
        ),
    ]