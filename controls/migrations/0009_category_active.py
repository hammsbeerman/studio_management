# Generated by Django 4.2.9 on 2024-02-17 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0008_inventorycategory_category_inventory_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='active',
            field=models.BooleanField(blank=True, default=True, null=True, verbose_name='Active'),
        ),
    ]
