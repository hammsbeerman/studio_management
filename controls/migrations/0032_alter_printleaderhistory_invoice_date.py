# Generated by Django 4.2.9 on 2024-07-22 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0031_printleaderhistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printleaderhistory',
            name='invoice_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
