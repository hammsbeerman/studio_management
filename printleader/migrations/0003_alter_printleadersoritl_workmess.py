# Generated by Django 4.2.9 on 2024-07-26 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('printleader', '0002_printleaderarinvoda_printleadersoordedt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printleadersoritl',
            name='Workmess',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Workmess'),
        ),
    ]