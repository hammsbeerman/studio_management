# Generated by Django 4.2.9 on 2024-04-03 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_profile_job_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='primary_company',
            field=models.CharField(choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], default='LK Design', max_length=100, verbose_name='Internal Company'),
            preserve_default=False,
        ),
    ]