from django.db import migrations, models
import django.db.models.deletion


def set_default_uoms(apps, schema_editor):
    InventoryMaster = apps.get_model("inventory", "InventoryMaster")
    InventoryQtyVariations = apps.get_model("inventory", "InventoryQtyVariations")

    # For each master item:
    # - If it has variations and none are default sell/receive,
    #   set the first ACTIVE variation as both defaults.
    masters = InventoryMaster.objects.all().only("id")
    for m in masters.iterator():
        qs = InventoryQtyVariations.objects.filter(inventory_id=m.id)
        if not qs.exists():
            continue

        has_default_sell = qs.filter(is_default_sell_uom=True).exists()
        has_default_recv = qs.filter(is_default_receive_uom=True).exists()

        if has_default_sell and has_default_recv:
            continue

        # pick first active if you have 'active', else just first
        first = qs.filter(active=True).order_by("id").first() or qs.order_by("id").first()
        if not first:
            continue

        update_fields = []
        if not has_default_sell:
            first.is_default_sell_uom = True
            update_fields.append("is_default_sell_uom")
        if not has_default_recv:
            first.is_default_receive_uom = True
            update_fields.append("is_default_receive_uom")

        if update_fields:
            first.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0071_inventoryqtyvariations_retail_price"),
        ("controls", "0044_alter_paymenttype_detail_field")
    ]

    operations = [
        # -------------------------
        # InventoryMaster additions
        # -------------------------
        migrations.AddField(
            model_name="inventorymaster",
            name="ledger_initialized",
            field=models.BooleanField(
                default=False,
                help_text="True once opening balance has been seeded into InventoryLedger for this item.",
            ),
        ),
        migrations.AddField(
            model_name="inventorymaster",
            name="legacy_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="inventorymaster",
            name="allow_price_override",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="inventorymaster",
            name="max_discount_percent_without_override",
            field=models.DecimalField(
                max_digits=6,
                decimal_places=2,
                null=True,
                blank=True,
                help_text="Max % discount allowed without manager override. Example: 15.00",
            ),
        ),
        migrations.AddField(
            model_name="inventorymaster",
            name="price_floor",
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text="Absolute minimum unit price allowed without manager override.",
            ),
        ),
        migrations.AddField(
            model_name="inventorymaster",
            name="min_margin_percent",
            field=models.DecimalField(
                max_digits=6,
                decimal_places=2,
                null=True,
                blank=True,
                help_text="Minimum margin % over unit_cost required without manager override.",
            ),
        ),
        migrations.AddField(
            model_name="inventorymaster",
            name="require_price_override_reason",
            field=models.BooleanField(default=False),
        ),

        # ---------------------------------
        # InventoryQtyVariations additions
        # ---------------------------------
        migrations.AddField(
            model_name="inventoryqtyvariations",
            name="is_default_sell_uom",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="inventoryqtyvariations",
            name="is_default_receive_uom",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="inventoryqtyvariations",
            name="allow_fractional_qty",
            field=models.BooleanField(
                default=False,
                help_text="If true, POS/receiving can use fractional quantities in this UOM.",
            ),
        ),
        migrations.AddField(
            model_name="inventoryqtyvariations",
            name="rounding_increment",
            field=models.DecimalField(
                max_digits=12,
                decimal_places=4,
                null=True,
                blank=True,
                help_text="Optional rounding step for quantity entry (e.g. 1.0000 for whole packs).",
            ),
        ),
        migrations.AddField(
            model_name="inventoryqtyvariations",
            name="active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddIndex(
            model_name="inventoryqtyvariations",
            index=models.Index(fields=["inventory", "variation"], name="inv_var_inv_var_idx"),
        ),

        # -------------------------
        # Optional: legacy mapping
        # -------------------------
        migrations.CreateModel(
            name="InventoryLegacyMapping",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("legacy_inventory_id", models.IntegerField(unique=True)),
                ("note", models.CharField(max_length=255, blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(
                    to="auth.user",  # if you use a custom user model, change to settings.AUTH_USER_MODEL via swappable dep (see below)
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="+",
                )),
                ("master", models.ForeignKey(
                    to="inventory.inventorymaster",
                    on_delete=django.db.models.deletion.CASCADE,
                )),
            ],
        ),

        # -------------------------
        # Data migration defaults
        # -------------------------
        migrations.RunPython(set_default_uoms, migrations.RunPython.noop),
    ]