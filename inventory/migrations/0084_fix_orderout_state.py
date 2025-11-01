from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        # point this at your latest applied inventory migration
        ("inventory", "0083_remove_orderout_oo_not_both_open_and_billed_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # don't touch the DB
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="orderout",
                    name="oo_not_both_open_and_billed",
                ),
                migrations.RemoveConstraint(
                    model_name="orderout",
                    name="oo_purchase_price_nonneg",
                ),
                migrations.RemoveConstraint(
                    model_name="orderout",
                    name="oo_percent_markup_nonneg",
                ),
                migrations.RemoveConstraint(
                    model_name="orderout",
                    name="oo_quantity_nonneg",
                ),
                migrations.RemoveConstraint(
                    model_name="orderout",
                    name="oo_unit_price_nonneg",
                ),
                migrations.RemoveConstraint(
                    model_name="orderout",
                    name="oo_total_price_nonneg",
                ),
            ],
        ),
    ]