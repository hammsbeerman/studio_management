# Generated by Django 4.2.9 on 2024-03-18 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0020_setpriceitem_created_setpriceitem_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='subcategory',
            name='inventory_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='controls.inventorycategory'),
        ),
    ]
