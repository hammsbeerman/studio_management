# Generated by Django 4.2.9 on 2024-03-07 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0023_alter_workorderitem_assigned_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='amount_paid',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Amount Paid'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='date_billed',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='date_paid',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='open_balance',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Open Balance'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='total_balance',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Total Balance'),
        ),
    ]
