# Generated by Django 4.2.9 on 2024-03-11 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0027_workorder_days_to_pay_alter_workorder_paid_in_full'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='aging',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Aging'),
        ),
    ]