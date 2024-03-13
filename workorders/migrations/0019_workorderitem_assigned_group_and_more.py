# Generated by Django 4.2.9 on 2024-03-06 16:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('controls', '0014_jobstatus_icon'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workorders', '0018_alter_workorder_customer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='assigned_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.group'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='assigned_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='job_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.jobstatus'),
        ),
    ]