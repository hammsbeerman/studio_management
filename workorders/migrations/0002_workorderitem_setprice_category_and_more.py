# Generated by Django 4.2.9 on 2024-02-13 14:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0005_alter_setpriceitemprice_set_quantity'),
        ('workorders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='setprice_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.setpriceitem'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='setprice_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.setpriceitemprice'),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='item_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='controls.category'),
        ),
    ]