# Generated by Django 4.2.9 on 2024-09-06 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0034_groupcategory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupcategory',
            name='name',
            field=models.CharField(default='x', max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
    ]
