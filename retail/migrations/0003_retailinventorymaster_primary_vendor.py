# Generated by Django 4.2.9 on 2024-08-18 18:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0033_vendor_retail_vendor'),
        ('retail', '0002_remove_retailinventorymaster_primary_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailinventorymaster',
            name='primary_vendor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.vendor'),
        ),
    ]