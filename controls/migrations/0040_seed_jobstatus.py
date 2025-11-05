from django.db import migrations

def seed(apps, schema_editor):
    JobStatus = apps.get_model("controls", "JobStatus")
    for n in ["Open", "Quoted"]:
        JobStatus.objects.get_or_create(name=n, defaults={"icon": ""})

class Migration(migrations.Migration):
    dependencies = [("controls", "0039_alter_groupcategory_id")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]