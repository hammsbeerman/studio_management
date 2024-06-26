# Generated by Django 4.2.9 on 2024-06-06 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0027_retailinventorycategory_icon_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailinventorycategory',
            name='description',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Description'),
        ),
        migrations.RemoveField(
            model_name='retailinventorysubcategory',
            name='inventory_category',
        ),
        migrations.AddField(
            model_name='retailinventorysubcategory',
            name='inventory_category',
            field=models.ManyToManyField(to='controls.retailinventorycategory'),
        ),
    ]