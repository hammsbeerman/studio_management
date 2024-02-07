# Generated by Django 4.2.9 on 2024-02-07 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccountsPayable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_recieved', models.DateField()),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('invoice_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Invoice Number')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Amount')),
                ('discount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Discount')),
                ('discount_date_due', models.DateField(blank=True, null=True)),
                ('paid', models.BooleanField(default=False, null=True, verbose_name='Paid')),
                ('date_paid', models.DateField(blank=True, null=True)),
                ('amount_paid', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Amount Paid')),
                ('payment_method', models.CharField(blank=True, choices=[('Cash', 'Cash'), ('Check', 'Check'), ('Credit Card', 'Credit Card'), ('Trade', 'Trade'), ('Other', 'Other')], max_length=100, null=True, verbose_name='Payment Method')),
            ],
        ),
        migrations.CreateModel(
            name='DailySales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('cash', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Cash')),
                ('checks', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Checks')),
                ('creditcard', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Credit Card')),
                ('creditcard_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Credit Card Fee')),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Total')),
            ],
        ),
    ]
