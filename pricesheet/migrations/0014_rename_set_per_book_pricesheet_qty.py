# Generated by Django 4.2.9 on 2024-03-27 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pricesheet', '0013_alter_pricesheet_side_2_inktype_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pricesheet',
            old_name='set_per_book',
            new_name='qty',
        ),
    ]