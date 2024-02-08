# Generated by Django 4.2.9 on 2024-02-05 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricesheet', '0005_alter_pricesheet_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='FixedCosts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('value', models.PositiveIntegerField(verbose_name='Value')),
            ],
        ),
        migrations.AlterField(
            model_name='pricesheet',
            name='press_sheet_per_parent',
            field=models.PositiveBigIntegerField(blank=True, null=True, verbose_name='Press sheets / Parent'),
        ),
    ]