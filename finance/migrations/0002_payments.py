# Generated by Django 4.2.9 on 2024-03-07 19:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0017_paymenttype'),
        ('workorders', '0024_workorder_amount_paid_workorder_date_billed_and_more'),
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Amount')),
                ('payment_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='controls.paymenttype')),
                ('workorder', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='workorders.workorder')),
            ],
        ),
    ]