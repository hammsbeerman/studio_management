# Generated by Django 4.2.9 on 2024-02-04 14:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('address1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Address 1')),
                ('address2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Adddress 2')),
                ('city', models.CharField(max_length=100, null=True, verbose_name='City')),
                ('state', models.CharField(max_length=100, null=True, verbose_name='State')),
                ('zipcode', models.CharField(blank=True, max_length=100, null=True, verbose_name='Zipcode')),
                ('phone1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone 1')),
                ('phone2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone 2')),
                ('email', models.EmailField(blank=True, max_length=100, null=True, verbose_name='Email')),
                ('website', models.URLField(blank=True, max_length=100, null=True, verbose_name='Website')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='VendorContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fname', models.CharField(blank=True, max_length=100, null=True, verbose_name='First Name')),
                ('lname', models.CharField(blank=True, max_length=100, null=True, verbose_name='Last Name')),
                ('phone1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone')),
                ('email', models.EmailField(blank=True, max_length=100, null=True, verbose_name='Email')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='vendors.vendor')),
            ],
        ),
    ]
