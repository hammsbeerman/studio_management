# Generated by Django 4.2.9 on 2024-11-12 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0044_alter_accountspayable_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountspayable',
            name='check_number',
            field=models.CharField(blank=True, max_length=30, verbose_name='Check Number'),
        ),
    ]
