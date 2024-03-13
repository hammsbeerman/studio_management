# Generated by Django 4.2.9 on 2024-03-03 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_alter_inventorydetail_item_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='height',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Height'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='width',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Width'),
        ),
    ]