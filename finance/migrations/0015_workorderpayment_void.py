# Generated by Django 4.2.9 on 2024-06-04 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0014_alter_payments_workorder_workorderpayment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderpayment',
            name='void',
            field=models.BooleanField(default=False, verbose_name='Void Payment'),
        ),
    ]
