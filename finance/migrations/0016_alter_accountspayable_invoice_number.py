# Generated by Django 4.2.9 on 2024-08-19 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0015_workorderpayment_void'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountspayable',
            name='invoice_number',
            field=models.CharField(max_length=100, null=True, verbose_name='Invoice Number'),
        ),
    ]