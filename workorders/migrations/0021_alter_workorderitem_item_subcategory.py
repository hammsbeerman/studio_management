# Generated by Django 4.2.9 on 2024-02-04 00:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0020_category_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorderitem',
            name='item_subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workorders.subcategory'),
        ),
    ]
