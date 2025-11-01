from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):
    # 🔁 update dependency to your latest inventory migration
    dependencies = [
        ('inventory', '0071_perf_indexes'),
    ]

    operations = [
        # Can't be both open and billed at the same time
        migrations.AddConstraint(
            model_name='orderout',
            constraint=models.CheckConstraint(
                check=~Q(open=True, billed=True),
                name='oo_not_both_open_and_billed',
            ),
        ),

        # Non-negative money/qty fields (allow NULL)
        migrations.AddConstraint(
            model_name='orderout',
            constraint=models.CheckConstraint(
                check=Q(purchase_price__gte=0) | Q(purchase_price__isnull=True),
                name='oo_purchase_price_nonneg',
            ),
        ),
        migrations.AddConstraint(
            model_name='orderout',
            constraint=models.CheckConstraint(
                check=Q(percent_markup__gte=0) | Q(percent_markup__isnull=True),
                name='oo_percent_markup_nonneg',
            ),
        ),
        migrations.AddConstraint(
            model_name='orderout',
            constraint=models.CheckConstraint(
                check=Q(quantity__gte=0) | Q(quantity__isnull=True),
                name='oo_quantity_nonneg',
            ),
        ),
        migrations.AddConstraint(
            model_name='orderout',
            constraint=models.CheckConstraint(
                check=Q(unit_price__gte=0) | Q(unit_price__isnull=True),
                name='oo_unit_price_nonneg',
            ),
        ),
        migrations.AddConstraint(
            model_name='orderout',
            constraint=models.CheckConstraint(
                check=Q(total_price__gte=0) | Q(total_price__isnull=True),
                name='oo_total_price_nonneg',
            ),
        ),
    ]