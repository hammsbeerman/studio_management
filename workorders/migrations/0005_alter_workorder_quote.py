# Generated by Django 4.2.9 on 2024-02-14 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0004_alter_workorder_quote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorder',
            name='quote',
            field=models.BooleanField(choices=[('1', 'Quote'), ('0', 'Workorder')], default=False, verbose_name='Quote'),
        ),
    ]