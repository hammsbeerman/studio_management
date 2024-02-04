# Generated by Django 4.2.9 on 2024-01-24 17:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0008_alter_contact_fname'),
        ('krueger', '0002_alter_kruegerjobdetail_jobnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kruegerjobdetail',
            name='company',
            field=models.CharField(blank=True, choices=[('LK', 'Lk'), ('KRUEGER', 'Krueger')], max_length=100, null=True, verbose_name='Company'),
        ),
        migrations.AlterField(
            model_name='kruegerjobdetail',
            name='customer',
            field=models.ForeignKey(blank=True, default=2, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='customers.customer'),
        ),
        migrations.AlterField(
            model_name='kruegerjobdetail',
            name='description',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Job Description'),
        ),
        migrations.AlterField(
            model_name='kruegerjobdetail',
            name='jobquote',
            field=models.CharField(choices=[('Workorder', 'Workorder'), ('Quote', 'Quote'), ('Template', 'Template')], max_length=100, verbose_name='Job Type'),
        ),
    ]