# Generated by Django 4.2.9 on 2024-07-29 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0031_inventorymaster'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='name',
            field=models.CharField(default='X', max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
    ]
