# Generated by Django 4.2.9 on 2024-10-23 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0012_remove_mailingcustomer_notes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mailingcustomer',
            options={'ordering': ['company_name', 'last_name']},
        ),
    ]