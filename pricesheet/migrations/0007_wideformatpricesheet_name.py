# Generated by Django 4.2.9 on 2024-03-01 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricesheet', '0006_remove_wideformatpricesheet_billed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='wideformatpricesheet',
            name='name',
            field=models.CharField(default='None', max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
    ]
