# Generated by Django 4.2.9 on 2025-02-24 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0014_customer_mail_bounced_back'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='mail_bounced_back',
            field=models.BooleanField(default=False, verbose_name='Mail Bounced Back'),
        ),
    ]
