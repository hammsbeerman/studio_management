from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0078_price_group_to_through'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderout',
            options={},   # or whatever options you intended
        ),
        migrations.AlterField(
            model_name='orderout',
            name='internal_company',
            field=models.CharField(
                'Internal Company',
                max_length=32,
                choices=[
                    ('LK Design', 'LK Design'),
                    ('Krueger Printing', 'Krueger Printing'),
                    ('Office Supplies', 'Office Supplies'),
                ],
            ),
        ),
        # IMPORTANT: no RemoveConstraint calls here.
    ]