# Generated by Django 4.2.9 on 2024-02-10 18:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0034_category_modelname_alter_category_modal'),
        ('customers', '0010_customer_customer_number_alter_customer_tax_exempt'),
        ('inventory', '0008_setprice_billed_setprice_dateentered_setprice_edited_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='setprice',
            name='subcategory',
            field=models.ForeignKey(blank=True, max_length=100, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='workorders.subcategory'),
        ),
        migrations.CreateModel(
            name='Photography',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hr_workorder', models.CharField(blank=True, max_length=100, null=True, verbose_name='Human Readable Workorder')),
                ('workorder_item', models.CharField(blank=True, max_length=100, null=True, verbose_name='Workorder Item')),
                ('internal_company', models.CharField(choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, verbose_name='Internal Company')),
                ('hr_customer', models.CharField(blank=True, max_length=100, null=True, verbose_name='Customer Name')),
                ('category', models.CharField(blank=True, max_length=10, null=True, verbose_name='Category')),
                ('subcategory', models.CharField(blank=True, max_length=10, null=True, verbose_name='Subcategory')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Quantity')),
                ('unit_price', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True, verbose_name='Unit Price')),
                ('total_price', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Total Price')),
                ('override_price', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Override Price')),
                ('last_item_order', models.CharField(blank=True, max_length=100, null=True, verbose_name='Original Item Order')),
                ('last_item_price', models.CharField(blank=True, max_length=100, null=True, verbose_name='Original Item Price')),
                ('notes', models.TextField(blank=True, verbose_name='Notes:')),
                ('dateentered', models.DateTimeField(auto_now_add=True)),
                ('billed', models.BooleanField(default=False, verbose_name='Billed')),
                ('edited', models.BooleanField(default=False, verbose_name='Edited')),
                ('customer', models.ForeignKey(blank=True, default=2, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='customers.customer')),
                ('workorder', models.ForeignKey(max_length=100, on_delete=django.db.models.deletion.CASCADE, to='workorders.workorder')),
            ],
        ),
    ]
