# Generated by Django 4.2.9 on 2024-02-16 15:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_setprice_category'),
        ('pricesheet', '0002_alter_pricesheet_paper_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='pricesheet',
            name='packaging',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='boxtype', to='inventory.inventory'),
        ),
    ]
