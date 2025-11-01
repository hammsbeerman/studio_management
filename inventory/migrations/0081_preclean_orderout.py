from django.db import migrations

def preclean(apps, schema_editor):
    OrderOut = apps.get_model('inventory', 'OrderOut')
    fields = ['purchase_price','percent_markup','quantity','unit_price','total_price']

    # Null out any negative numeric fields to satisfy non-negative OR NULL checks
    for row in OrderOut.objects.only('id', *fields):
        updates = {}
        for f in fields:
            v = getattr(row, f, None)
            if v is not None and v < 0:
                updates[f] = None
        if updates:
            OrderOut.objects.filter(pk=row.id).update(**updates)

    # Ensure no rows are both open and billed
    OrderOut.objects.filter(open=True, billed=True).update(open=False)

class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0080_remove_orderout_oo_not_both_open_and_billed_and_more"),
    ]

    operations = [
        migrations.RunPython(preclean, migrations.RunPython.noop),
    ]