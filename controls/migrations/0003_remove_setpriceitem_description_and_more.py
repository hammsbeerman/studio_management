# Generated by Django 4.2.9 on 2024-02-12 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0002_setpriceitem_category_setpriceitem_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='setpriceitem',
            name='description',
        ),
        migrations.AlterField(
            model_name='setpriceitem',
            name='name',
            field=models.CharField(default='1', max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='setpriceitemprice',
            name='quantity',
            field=models.CharField(max_length=100, verbose_name='Quantity / Description'),
        ),
    ]
