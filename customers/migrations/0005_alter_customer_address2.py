# Generated by Django 4.2.9 on 2024-02-19 22:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0004_alter_contact_address2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='address2',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Adddress 2'),
        ),
    ]