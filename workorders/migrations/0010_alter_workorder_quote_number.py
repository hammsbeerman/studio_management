# Generated by Django 4.2.9 on 2024-02-18 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0009_rename_comleted_workorder_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorder',
            name='quote_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Quote Number'),
        ),
    ]
