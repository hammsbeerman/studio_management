# Generated by Django 4.2.9 on 2024-03-07 16:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_group_alter_profile_email_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workorders', '0022_alter_workorderitem_assigned_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorderitem',
            name='assigned_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='test_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.profile'),
        ),
    ]
