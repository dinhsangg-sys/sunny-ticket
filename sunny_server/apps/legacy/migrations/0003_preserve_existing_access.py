from django.db import migrations

def preserve(apps,schema_editor):
    User=apps.get_model('accounts','User')
    Group=apps.get_model('auth','Group')
    Permission=apps.get_model('auth','Permission')
    ContentType=apps.get_model('contenttypes','ContentType')
    ct,_=ContentType.objects.get_or_create(app_label='legacy',model='workspace')
    permission,_=Permission.objects.get_or_create(content_type=ct,codename='workspace__full_access',defaults={'name':'Toàn bộ dữ liệu/nghiệp vụ — chỉ nhân sự tin cậy'})
    group,_=Group.objects.get_or_create(name='Sunny - Quyền đầy đủ từ bản cũ')
    group.permissions.add(permission)
    for user in User.objects.filter(role__in=['admin','operator']): user.groups.add(group)

class Migration(migrations.Migration):
    dependencies=[('legacy','0002_alter_workspace_options')]
    operations=[migrations.RunPython(preserve,migrations.RunPython.noop)]
