from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help='Tạo nhóm quyền cho quầy bán vé; không tạo tài khoản hoặc sửa dữ liệu booking.'
    def handle(self,*args,**kwargs):
        permissions=Permission.objects.filter(content_type__app_label='legacy',codename__in=['counter__view','counter__create'])
        if permissions.count()!=2:raise CommandError('Chạy migrate trước để tạo đủ quyền quầy.')
        group,created=Group.objects.get_or_create(name='Nhân viên bán vé tại quầy')
        if not created and group.permissions.exclude(pk__in=permissions.values_list('pk',flat=True)).exists():
            raise CommandError('Nhóm cùng tên có quyền khác. Hãy đối soát, không tự sửa nhóm đang dùng.')
        group.permissions.add(*permissions)
        self.stdout.write(self.style.SUCCESS('Đã chuẩn bị nhóm Nhân viên bán vé tại quầy. Tạo user role counter, không staff/superuser, rồi gán nhóm này.'))
