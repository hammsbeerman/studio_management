# Generated by Django 4.2.9 on 2024-04-05 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0007_araging'),
    ]

    operations = [
        migrations.AddField(
            model_name='araging',
            name='hr_customer',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Customer'),
        ),
        migrations.AlterField(
            model_name='araging',
            name='current',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Current'),
        ),
        migrations.AlterField(
            model_name='araging',
            name='ninety',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Ninety'),
        ),
        migrations.AlterField(
            model_name='araging',
            name='onetwenty',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='One Twenty'),
        ),
        migrations.AlterField(
            model_name='araging',
            name='sixty',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Sixty'),
        ),
        migrations.AlterField(
            model_name='araging',
            name='thirty',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Thirty'),
        ),
        migrations.AlterField(
            model_name='araging',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Total'),
        ),
    ]
