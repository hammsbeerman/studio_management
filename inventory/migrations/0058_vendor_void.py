# Generated by Django 4.2.9 on 2024-10-03 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0057_alter_inventorymaster_high_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='void',
            field=models.BooleanField(default=False),
        ),
    ]
