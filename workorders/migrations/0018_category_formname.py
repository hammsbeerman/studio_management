# Generated by Django 4.2.9 on 2024-01-30 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0017_workorder_billed'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='formname',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Form'),
        ),
    ]
