# Generated by Django 4.2.9 on 2024-08-07 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0010_alter_retailinvoiceitem_internal_part_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='retailinvoiceitem',
            name='name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item_name', to='retail.retailinventorymaster'),
        ),
    ]
