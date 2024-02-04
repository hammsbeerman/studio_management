# Generated by Django 4.2.9 on 2024-01-25 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('krueger', '0005_rename_jobnumber_kruegerjobdetail_workorder_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='kruegerjobdetail',
            name='company',
        ),
        migrations.AddField(
            model_name='kruegerjobdetail',
            name='internal_company',
            field=models.CharField(choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], default='LK Design', max_length=100, verbose_name='Internal Company'),
            preserve_default=False,
        ),
    ]