# Generated by Django 4.2.9 on 2024-03-08 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0017_paymenttype'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymenttype',
            name='detail_field',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Name'),
        ),
    ]
