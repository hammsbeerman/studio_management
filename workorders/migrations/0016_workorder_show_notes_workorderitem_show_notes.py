# Generated by Django 4.2.9 on 2024-03-01 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0015_workorderitem_child'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='show_notes',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='show_notes',
            field=models.BooleanField(default=False),
        ),
    ]
