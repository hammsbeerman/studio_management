# Generated by Django 4.2.9 on 2024-02-13 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_alter_setprice_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='setprice',
            name='category',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Category'),
        ),
    ]
