from django.db import migrations

def hide_line(apps,schema_editor):
    # User explicitly removed LINE until a real account is created.
    apps.get_model('online','SiteContact').objects.using(schema_editor.connection.alias).filter(pk=1).update(line_phone='',line_url='')

class Migration(migrations.Migration):
    dependencies=[('online','0003_sitecontact')]
    operations=[migrations.RunPython(hide_line,migrations.RunPython.noop)]
