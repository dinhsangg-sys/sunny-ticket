import copy
from django.db import migrations, models
from django.utils import timezone


def mark_digital(apps, schema_editor):
    workspace = apps.get_model('legacy', 'Workspace')
    for obj in workspace.objects.using(schema_editor.connection.alias).select_for_update().all():
        data = copy.deepcopy(obj.data)
        changed = False
        for row in data.get('bookings', []):
            if row.get('salesChannel') == 'online' and row.get('agent') != 'Digital':
                row['agent'] = 'Digital'
                changed = True
        if changed:
            workspace.objects.using(schema_editor.connection.alias).filter(pk=obj.pk).update(
                data=data, revision=models.F('revision') + 1, updated_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('online', '0008_service_faq_chat')]
    operations = [migrations.RunPython(mark_digital, migrations.RunPython.noop)]
