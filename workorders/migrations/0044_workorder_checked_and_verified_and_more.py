# Generated by Django 4.2.9 on 2024-04-25 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0043_workorderitem_prequoted_workorderitem_quoted_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='checked_and_verified',
            field=models.BooleanField(default=False, verbose_name='Checked and Verified'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='delivered_or_pickedup',
            field=models.BooleanField(default=False, verbose_name='Delivered or Picked Up'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='delivery_pickup',
            field=models.CharField(choices=[('Delivery', 'Delivery'), ('Pickup', 'Pickup')], default='Delivery', max_length=100, verbose_name='Delivery or Pickup'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='invoice_sent',
            field=models.BooleanField(default=False, verbose_name='Invoice Sent'),
        ),
    ]
