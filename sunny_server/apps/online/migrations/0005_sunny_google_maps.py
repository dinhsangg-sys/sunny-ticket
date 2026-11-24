from django.db import migrations


def seed_google_maps(apps, schema_editor):
    model = apps.get_model('online', 'SiteContact')
    obj, _ = model.objects.using(schema_editor.connection.alias).get_or_create(pk=1)
    if not obj.google_maps_url:
        obj.google_maps_url = 'https://share.google/8FKS1V2zJ0mxKpJE4'
        obj.save(using=schema_editor.connection.alias, update_fields=['google_maps_url'])


class Migration(migrations.Migration):
    dependencies = [('online', '0004_hide_line_until_configured')]
    operations = [migrations.RunPython(seed_google_maps, migrations.RunPython.noop)]
