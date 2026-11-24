from urllib.parse import urlparse
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from apps.legacy.sepay import ready
from apps.legacy.counter_tickets import email_ready
from apps.online.views import owner
from apps.online.models import Service,OnlinePrice
class Command(BaseCommand):
    help='Kiểm tra cấu hình online, không in khóa bí mật hoặc tài khoản ngân hàng.'
    def handle(self,*args,**options):
        origin=settings.PUBLIC_SITE_URL
        host=urlparse(origin).hostname
        checks=[('PUBLIC_SITE_URL dùng HTTPS',urlparse(origin).scheme=='https' and bool(host)),('Host công khai khớp tên miền',host in settings.PUBLIC_SITE_HOSTS),('ALLOWED_HOSTS chấp nhận tên miền',host in settings.ALLOWED_HOSTS),('CSRF tin cậy tên miền',origin in settings.CSRF_TRUSTED_ORIGINS),('Người phụ trách là superuser đang hoạt động',owner() is not None),('SePay sẵn sàng',ready()),('Email gửi vé sẵn sàng',email_ready()),('Có dịch vụ công khai',Service.objects.filter(published=True).exists()),('Có bảng giá online đang bật',OnlinePrice.objects.filter(active=True).exists())]
        self.stdout.write('Website: '+origin)
        self.stdout.write('Thanh toán mới: '+('BẬT' if settings.ONLINE_CHECKOUT_ENABLED else 'TẮT'))
        self.stdout.write('Môi trường SePay: '+settings.SEPAY_MODE)
        for label,ok in checks:self.stdout.write(('OK: ' if ok else 'CHƯA ĐẠT: ')+label)
        self.stdout.write('Lưu ý: chưa kiểm tra DNS, HTTPS công khai, giao dịch thật, SMTP thực tế hay tồn vé của nhà cung cấp.')
        if settings.ONLINE_CHECKOUT_ENABLED and not all(ok for _,ok in checks):raise CommandError('Chưa đủ cấu hình để mở thanh toán online. Tắt ONLINE_CHECKOUT_ENABLED cho đến khi hoàn tất.')
