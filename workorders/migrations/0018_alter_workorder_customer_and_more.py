# Generated by Django 4.2.9 on 2024-03-01 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0006_alter_contact_customer'),
        ('controls', '0011_alter_category_pricesheet_type_and_more'),
        ('workorders', '0017_workorderitem_postage_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorder',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workorders', to='customers.customer'),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='design_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.designtype'),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='item_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.category'),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='postage_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.postagetype'),
        ),
        migrations.AlterField(
            model_name='workorderitem',
            name='workorder',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='workorders.workorder'),
        ),
    ]