# Generated by Django 4.2.9 on 2024-08-16 17:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='retailinvoiceitem',
            name='invoice',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='retail.retailinvoices'),
        ),
    ]
