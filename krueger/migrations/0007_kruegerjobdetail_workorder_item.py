# Generated by Django 4.2.9 on 2024-01-25 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('krueger', '0006_remove_kruegerjobdetail_company_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='kruegerjobdetail',
            name='workorder_item',
            field=models.CharField(default='1', max_length=100, verbose_name='Workorder Item'),
            preserve_default=False,
        ),
    ]
