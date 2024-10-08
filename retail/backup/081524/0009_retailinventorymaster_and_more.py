# Generated by Django 4.2.9 on 2024-08-07 13:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('retail', '0008_alter_retailinvoiceitem_qty_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RetailInventoryMaster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('high_price', models.CharField(blank=True, max_length=100, null=True, verbose_name='High Price')),
            ],
        ),
        migrations.AlterField(
            model_name='retailitemdetail',
            name='internal_part_number',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='retail.retailinventorymaster'),
            preserve_default=False,
        ),
    ]
