# Generated by Django 4.2.9 on 2025-02-24 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0013_alter_mailingcustomer_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='mail_bounced_back',
            field=models.BooleanField(choices=[(True, 'Yes'), (False, 'No')], default=False, verbose_name='Mail Bounced Back'),
        ),
    ]
