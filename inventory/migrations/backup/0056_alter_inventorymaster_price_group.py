# Generated by Django 4.2.9 on 2024-09-06 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0035_alter_groupcategory_name'),
        ('inventory', '0055_inventorymaster_grouped_inventorymaster_price_group_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorymaster',
            name='price_group',
            field=models.ManyToManyField(blank=True, to='controls.groupcategory'),
        ),
    ]
