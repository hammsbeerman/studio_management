# Generated by Django 4.2.9 on 2024-06-26 15:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0009_shipto'),
        ('workorders', '0048_alter_workorder_date_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='ship_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='customers.shipto'),
        ),
    ]
