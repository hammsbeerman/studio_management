# Generated by Django 4.2.9 on 2024-01-30 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('krueger', '0012_kruegerjobdetail_edited'),
    ]

    operations = [
        migrations.AddField(
            model_name='kruegerjobdetail',
            name='category',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Category'),
        ),
        migrations.AddField(
            model_name='kruegerjobdetail',
            name='subcategory',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Subcategory'),
        ),
    ]
