# Generated by Django 4.2.9 on 2024-01-15 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fname', models.CharField(blank=True, max_length=100, null=True, verbose_name='First Name')),
                ('lname', models.CharField(blank=True, max_length=100, null=True, verbose_name='Last Name')),
                ('address1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Address 1')),
                ('address2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Adddress 2')),
                ('city', models.CharField(blank=True, max_length=100, null=True, verbose_name='City')),
                ('state', models.CharField(blank=True, max_length=100, null=True, verbose_name='State')),
                ('zipcode', models.CharField(blank=True, max_length=100, null=True, verbose_name='Zipcode')),
                ('phone1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone')),
                ('email', models.EmailField(blank=True, max_length=100, null=True, verbose_name='Email')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='customercontact',
            name='customer',
        ),
    ]
