# Generated by Django 4.2.9 on 2024-02-18 17:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0008_workorder_comleted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workorder',
            old_name='comleted',
            new_name='completed',
        ),
    ]
