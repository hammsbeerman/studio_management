# Generated by Django 4.2.9 on 2024-09-06 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0033_delete_printleaderhistory'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Name')),
            ],
        ),
    ]