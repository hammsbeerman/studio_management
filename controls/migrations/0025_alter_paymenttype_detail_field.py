# Generated by Django 4.2.9 on 2024-04-19 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0024_rename_setpriceitem_setpricecategory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenttype',
            name='detail_field',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Detail Field'),
        ),
    ]
