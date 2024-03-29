# Generated by Django 4.2.9 on 2024-03-07 23:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_group_alter_profile_email_and_more'),
        ('workorders', '0024_workorder_amount_paid_workorder_date_billed_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workorderitem',
            name='test_user',
        ),
        migrations.AlterField(
            model_name='workorder',
            name='amount_paid',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Amount Paid'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='open_balance',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Open Balance'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='total_balance',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Total Balance'),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='assigned_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.profile'),
        ),
    ]
