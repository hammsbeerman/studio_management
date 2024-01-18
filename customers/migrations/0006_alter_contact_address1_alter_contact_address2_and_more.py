# Generated by Django 4.2.9 on 2024-01-16 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0005_alter_customer_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='address1',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Address 1'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='address2',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Adddress 2'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='City'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=100, verbose_name='Email'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='fname',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='First Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='lname',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Last Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone1',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Phone'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='state',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='State'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='zipcode',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Zipcode'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='address1',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Address 1'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='address2',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Adddress 2'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='City'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='company_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Company Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=100, verbose_name='Email'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='First Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone1',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Phone 1'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone2',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Phone 2'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='state',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='State'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='website',
            field=models.URLField(blank=True, default='', max_length=100, verbose_name='Website'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='zipcode',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Zipcode'),
            preserve_default=False,
        ),
    ]
