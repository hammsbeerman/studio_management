# Generated by Django 4.2.9 on 2024-04-19 16:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0038_workorder_quickbooks_workorder_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workorder',
            old_name='quickbooks_workorder',
            new_name='kos_workorder',
        ),
    ]
