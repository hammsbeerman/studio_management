# Generated by Django 4.2.9 on 2024-08-26 17:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0033_delete_printleaderhistory'),
        ('inventory', '0043_inventorypricinggroup_high_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemqtyvariations',
            name='measurement',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='controls.measurement'),
        ),
    ]