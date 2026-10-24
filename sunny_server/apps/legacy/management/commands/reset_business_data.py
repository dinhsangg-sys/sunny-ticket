from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry
from django.conf import settings
from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.audit.models import AuditLog
from apps.legacy.models import Workspace,Attachment
from apps.legacy.pricing import COLLECTIONS
from apps.legacy.partners import partner_types

class Command(BaseCommand):
    help='Xóa toàn bộ dữ liệu nghiệp vụ và tệp đính kèm; giữ tài khoản/nhóm/quyền. Mặc định chỉ xem trước.'

    def add_arguments(self,parser):
        parser.add_argument('--execute',action='store_true',help='Thực hiện xóa dữ liệu nghiệp vụ trong database đang cấu hình.')

    def handle(self,*args,**options):
        counts={'workspace':Workspace.objects.count(),'agency':Agency.objects.count(),'attachment':Attachment.objects.count(),'audit':AuditLog.objects.count()}
        self.stdout.write('Database: '+str(settings.DATABASES['default']['NAME']))
        self.stdout.write('Sẽ xóa: '+str(counts))
        self.stdout.write('Giữ tài khoản, mật khẩu, nhóm và quyền. Gỡ liên kết đại lý của user; đăng xuất tất cả phiên.')
        if not options['execute']:
            self.stdout.write('Chỉ xem trước. Dùng --execute khi đã dừng server để thực hiện.')
            return
        files=list(Attachment.objects.all())
        fresh={k:[] for k in COLLECTIONS}
        fresh['partnerTypes']=partner_types({})
        fresh['settings']={'businessName':'Sunny Travel','currency':'VND','version':'1.10.1'}
        fresh['zaloSettings']={'reminderTemplate':'Sunny Travel xin chào {agent}! Booking {code} còn công nợ {due}. Xin cảm ơn!'}
        with transaction.atomic():
            User.objects.filter(agency__isnull=False).update(agency=None)
            Agency.objects.all().delete()
            AuditLog.objects.all().delete()
            LogEntry.objects.all().delete()
            Attachment.objects.all().delete()
            Workspace.objects.get_or_create(pk=1)
            # Increment instead of resetting the revision: stale browser tabs cannot restore old data.
            Workspace.objects.filter(pk=1).update(data=fresh,revision=F('revision')+1)
            Workspace.objects.exclude(pk=1).delete()
            Session.objects.all().delete()
        failures=[]
        for attachment in files:
            try: attachment.file.delete(save=False)
            except Exception: failures.append(attachment.file.name)
        if failures: raise CommandError('Database đã xóa; một số tệp chưa xóa được. Kiểm tra quyền kho media: '+', '.join(failures))
        self.stdout.write(self.style.SUCCESS('Đã xóa dữ liệu nghiệp vụ. Đăng nhập lại để khai báo mới.'))
