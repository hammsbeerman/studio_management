# Generated by Django 4.2.9 on 2024-05-28 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0047_workorder_payment_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorder',
            name='date_paid',
            field=models.DateField(blank=True, null=True),
        ),
    ]
