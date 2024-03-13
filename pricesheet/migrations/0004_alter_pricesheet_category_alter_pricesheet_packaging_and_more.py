# Generated by Django 4.2.9 on 2024-03-01 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_alter_inventorydetail_item_and_more'),
        ('controls', '0011_alter_category_pricesheet_type_and_more'),
        ('pricesheet', '0003_pricesheet_packaging'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pricesheet',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.category'),
        ),
        migrations.AlterField(
            model_name='pricesheet',
            name='packaging',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='boxtype', to='inventory.inventory'),
        ),
        migrations.AlterField(
            model_name='pricesheet',
            name='paper_stock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.inventory'),
        ),
    ]