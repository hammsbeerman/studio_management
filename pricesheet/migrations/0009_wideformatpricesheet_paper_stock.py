# Generated by Django 4.2.9 on 2024-03-01 22:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_alter_inventorydetail_item_and_more'),
        ('pricesheet', '0008_wideformatpricesheet_dateentered_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='wideformatpricesheet',
            name='paper_stock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.inventory'),
        ),
    ]