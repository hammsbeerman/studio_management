# Generated by Django 4.2.9 on 2024-03-21 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0024_rename_setpriceitem_setpricecategory'),
        ('accounts', '0002_profile_group_alter_profile_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='job_status',
            field=models.ManyToManyField(to='controls.jobstatus'),
        ),
    ]
