# Generated by Django 4.2.9 on 2024-03-03 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_inventory_type_mask'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='type_laminate',
            field=models.BooleanField(default=False, verbose_name='Laminate'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='type_substrate',
            field=models.BooleanField(default=False, verbose_name='Substrate'),
        ),
    ]
