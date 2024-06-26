# Generated by Django 4.2.9 on 2024-06-06 19:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0025_alter_paymenttype_detail_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='RetailCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('active', models.BooleanField(blank=True, default=True, null=True, verbose_name='Active')),
            ],
        ),
        migrations.CreateModel(
            name='RetailInventoryCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True, verbose_name='Name')),
            ],
        ),
        migrations.CreateModel(
            name='RetailSubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Category', to='controls.retailcategory')),
                ('inventory_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='controls.retailinventorycategory')),
            ],
        ),
        migrations.AddField(
            model_name='retailcategory',
            name='inventory_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='controls.retailinventorycategory'),
        ),
    ]
