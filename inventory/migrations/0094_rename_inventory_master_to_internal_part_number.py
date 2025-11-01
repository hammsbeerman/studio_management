from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0093_delete_workorderitem"),
    ]

    operations = [
        migrations.RenameField(
            model_name="inventory",
            old_name="master",
            new_name="internal_part_number",
        ),
    ]