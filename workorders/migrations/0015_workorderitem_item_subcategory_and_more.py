# Generated by Django 4.2.9 on 2024-01-24 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0014_remove_category_subcategory_subcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='item_subcategory',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Subcategory'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='pricesheet_modified',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Pricesheet Modified'),
        ),
    ]