# Generated by Django 4.2.9 on 2024-05-28 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0046_workorder_orderout_waiting'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='payment_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Payment ID'),
        ),
    ]