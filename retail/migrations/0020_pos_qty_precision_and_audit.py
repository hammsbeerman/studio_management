from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("retail", "0019_retailsaleline_is_gift_certificate"),  # <-- change to your last migration
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Increase qty precision to support fractional units like ft/lb/etc.
        migrations.AlterField(
            model_name="retailsaleline",
            name="qty",
            field=models.DecimalField(
                max_digits=10,
                decimal_places=4,
                default=Decimal("1.0000"),
            ),
        ),

        migrations.CreateModel(
            name="RetailSaleLineAudit",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),

                ("action", models.CharField(
                    max_length=32,
                    choices=[
                        ("PRICE_OVERRIDE", "Price override"),
                        ("ITEM_SWAP", "Item swap"),
                        ("UOM_CHANGE", "UOM change"),
                        ("QTY_CHANGE", "Qty change"),
                    ],
                )),

                ("old_unit_price", models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ("new_unit_price", models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),

                ("old_inventory_id", models.IntegerField(null=True, blank=True)),
                ("new_inventory_id", models.IntegerField(null=True, blank=True)),

                ("old_variation_id", models.IntegerField(null=True, blank=True)),
                ("new_variation_id", models.IntegerField(null=True, blank=True)),

                ("old_qty", models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)),
                ("new_qty", models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)),

                ("reason", models.CharField(max_length=255, blank=True, default="")),

                ("manager_user", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="pos_line_override_approvals",
                )),
                ("user", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="pos_line_audits",
                )),
                ("sale_line", models.ForeignKey(
                    to="retail.retailsaleline",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="audits",
                )),
            ],
        ),
    ]