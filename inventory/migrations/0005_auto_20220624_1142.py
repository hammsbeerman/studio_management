# Generated by Django 3.2.13 on 2022-06-24 16:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_auto_20220528_1807'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='measurement',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='service',
            options={'ordering': ['category', 'name']},
        ),
    ]
