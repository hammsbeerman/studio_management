# Generated by Django 4.2.9 on 2024-03-06 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0019_workorderitem_assigned_group_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]