# Generated by Django 4.2.9 on 2024-09-16 21:44

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0040_allinvoiceitem_line_total_allinvoiceitem_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='allinvoiceitem',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='allinvoiceitem',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='allinvoiceitem',
            name='invoice_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='finance.accountspayable'),
        ),
    ]