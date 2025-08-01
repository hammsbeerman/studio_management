# Generated by Django 4.2.9 on 2025-07-29 21:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0015_alter_customer_mail_bounced_back'),
        ('finance', '0046_alter_workorderpayment_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Krueger_Araging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hr_customer', models.CharField(blank=True, max_length=500, null=True, verbose_name='Customer')),
                ('date', models.DateField()),
                ('current', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Current')),
                ('thirty', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Thirty')),
                ('sixty', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Sixty')),
                ('ninety', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Ninety')),
                ('onetwenty', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='One Twenty')),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Total')),
                ('customer', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='customers.customer')),
            ],
        ),
    ]
