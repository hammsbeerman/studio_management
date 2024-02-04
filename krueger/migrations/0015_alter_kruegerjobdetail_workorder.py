# Generated by Django 4.2.9 on 2024-02-04 20:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0024_workorder_tax_exempt'),
        ('krueger', '0014_kruegerjobdetail_last_item_order_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kruegerjobdetail',
            name='workorder',
            field=models.ForeignKey(max_length=100, on_delete=django.db.models.deletion.CASCADE, to='workorders.workorder'),
        ),
    ]
