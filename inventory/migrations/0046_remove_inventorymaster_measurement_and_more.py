# Generated by Django 4.2.9 on 2024-09-03 14:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0033_delete_printleaderhistory'),
        ('inventory', '0045_inventoryqtyvariations_variation_qty'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorymaster',
            name='measurement',
        ),
        migrations.AddField(
            model_name='inventorymaster',
            name='primary_base_unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.measurement'),
        ),
    ]