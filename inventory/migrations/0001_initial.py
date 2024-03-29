# Generated by Django 4.2.9 on 2024-02-12 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('controls', '0001_initial'),
        ('customers', '0001_initial'),
        ('workorders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True, verbose_name='Name')),
                ('name2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Additional Name')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('internal_part_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Internal Part Number')),
                ('unit_cost', models.CharField(blank=True, max_length=100, null=True, verbose_name='Unit Cost')),
                ('price_per_m', models.CharField(blank=True, max_length=100, null=True, verbose_name='Paper Stock Price per M')),
                ('current_stock', models.CharField(blank=True, max_length=100, null=True, verbose_name='Current Stock')),
                ('color', models.CharField(blank=True, max_length=100, null=True, verbose_name='Color')),
                ('size', models.CharField(blank=True, max_length=100, null=True, verbose_name='Size')),
                ('type_paper', models.BooleanField(default=False, verbose_name='Paper')),
                ('type_envelope', models.BooleanField(default=False, verbose_name='Envelope')),
                ('type_wideformat', models.BooleanField(default=False, verbose_name='Wide Format')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('measurement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='controls.measurement')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendor_item_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Vendor Part Number')),
                ('test', models.CharField(blank=True, max_length=100, verbose_name='test')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.inventory')),
            ],
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('address1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Address 1')),
                ('address2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Adddress 2')),
                ('city', models.CharField(max_length=100, null=True, verbose_name='City')),
                ('state', models.CharField(max_length=100, null=True, verbose_name='State')),
                ('zipcode', models.CharField(blank=True, max_length=100, null=True, verbose_name='Zipcode')),
                ('phone1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone 1')),
                ('phone2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone 2')),
                ('email', models.EmailField(blank=True, max_length=100, null=True, verbose_name='Email')),
                ('website', models.URLField(blank=True, max_length=100, null=True, verbose_name='Website')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('inventorydetails', models.ManyToManyField(through='inventory.InventoryDetail', to='inventory.inventory')),
            ],
        ),
        migrations.CreateModel(
            name='VendorContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fname', models.CharField(blank=True, max_length=100, null=True, verbose_name='First Name')),
                ('lname', models.CharField(blank=True, max_length=100, null=True, verbose_name='Last Name')),
                ('phone1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone')),
                ('email', models.EmailField(blank=True, max_length=100, null=True, verbose_name='Email')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.vendor')),
            ],
        ),
        migrations.CreateModel(
            name='SetPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Name')),
                ('hr_workorder', models.CharField(blank=True, max_length=100, null=True, verbose_name='Human Readable Workorder')),
                ('workorder_item', models.CharField(blank=True, max_length=100, null=True, verbose_name='Workorder Item')),
                ('internal_company', models.CharField(choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, verbose_name='Internal Company')),
                ('hr_customer', models.CharField(blank=True, max_length=100, null=True, verbose_name='Customer Name')),
                ('category', models.CharField(blank=True, max_length=10, null=True, verbose_name='Category')),
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
                ('subcategory', models.ForeignKey(blank=True, max_length=100, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='controls.subcategory')),
                ('workorder', models.ForeignKey(max_length=100, on_delete=django.db.models.deletion.CASCADE, to='workorders.workorder')),
            ],
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
        migrations.CreateModel(
            name='OrderOut',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hr_workorder', models.CharField(blank=True, max_length=100, null=True, verbose_name='Human Readable Workorder')),
                ('workorder_item', models.CharField(blank=True, max_length=100, null=True, verbose_name='Workorder Item')),
                ('internal_company', models.CharField(choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, verbose_name='Internal Company')),
                ('hr_customer', models.CharField(blank=True, max_length=100, null=True, verbose_name='Customer Name')),
                ('category', models.CharField(blank=True, max_length=10, null=True, verbose_name='Category')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('purchase_price', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Purchase Price')),
                ('percent_markup', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Percent Markup')),
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
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='inventory.vendor')),
                ('workorder', models.ForeignKey(max_length=100, on_delete=django.db.models.deletion.CASCADE, to='workorders.workorder')),
            ],
        ),
        migrations.AddField(
            model_name='inventorydetail',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.vendor'),
        ),
    ]
