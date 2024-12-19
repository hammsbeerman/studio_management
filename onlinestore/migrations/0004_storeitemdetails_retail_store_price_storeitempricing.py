# Generated by Django 4.2.9 on 2024-12-01 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('onlinestore', '0003_storeitemvariation'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeitemdetails',
            name='retail_store_price',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=15, null=True, verbose_name='Retail Store Price'),
        ),
        migrations.CreateModel(
            name='StoreItemPricing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='onlinestore.storeitemdetails')),
            ],
        ),
    ]
