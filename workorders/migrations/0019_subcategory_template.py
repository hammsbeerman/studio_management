# Generated by Django 4.2.9 on 2024-01-31 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0018_category_formname'),
    ]

    operations = [
        migrations.AddField(
            model_name='subcategory',
            name='template',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Template'),
        ),
    ]