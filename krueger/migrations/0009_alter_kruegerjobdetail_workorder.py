# Generated by Django 4.2.9 on 2024-01-29 14:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0016_alter_workorderitem_workorder_hr'),
        ('krueger', '0008_kruegerjobdetail_billed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kruegerjobdetail',
            name='workorder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workorders.workorder'),
        ),
    ]
