# Generated by Django 4.2.9 on 2024-05-29 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0012_accountspayable_date_due'),
    ]

    operations = [
        migrations.AddField(
            model_name='payments',
            name='available',
            field=models.DecimalField(decimal_places=2, default=None, max_digits=10, null=True, verbose_name='Amount Available'),
        ),
    ]