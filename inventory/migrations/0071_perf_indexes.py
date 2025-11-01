from django.db import migrations, models

class Migration(migrations.Migration):
    # 👇 Replace '0070_alter_orderout_options_orderout_open_and_more'
    # with your latest inventory migration.
    dependencies = [
        ('inventory', '0070_alter_orderout_options_orderout_open_and_more'),
    ]

    operations = [
        # Fast lookup by name in the flat Inventory table (used in admin/search)
        migrations.AddIndex(
            model_name='inventory',
            index=models.Index(fields=['name'], name='inv_name_idx'),
        ),

        # Fast reporting/sorts on high_price
        migrations.AddIndex(
            model_name='inventorymaster',
            index=models.Index(fields=['high_price'], name='im_high_price_idx'),
        ),

        # Very common filter/order: recent orders by vendor
        migrations.AddIndex(
            model_name='orderout',
            index=models.Index(fields=['vendor', 'dateentered'], name='oo_vendor_date_idx'),
        ),

        # Cheap booleans used in list filters
        migrations.AddIndex(
            model_name='orderout',
            index=models.Index(fields=['billed'], name='oo_billed_idx'),
        ),
        migrations.AddIndex(
            model_name='orderout',
            index=models.Index(fields=['open'], name='oo_open_idx'),
        ),
    ]