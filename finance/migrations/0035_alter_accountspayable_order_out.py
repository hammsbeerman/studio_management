# Generated by Django 4.2.9 on 2024-09-11 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0034_accountspayable_non_inventory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountspayable',
            name='order_out',
            field=models.BooleanField(default=False, null=True, verbose_name='Order Out'),
        ),
    ]
