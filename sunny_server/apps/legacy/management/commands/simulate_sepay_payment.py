"""Exercise the signed webhook locally, exclusively against a test-mode intent."""
import hashlib
import hmac
import json
import uuid
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory
from django.utils import timezone
from apps.legacy.models import SePayIntent
from apps.legacy.sepay import ready, webhook


class Command(BaseCommand):
    help='Mô phỏng tiền vào SePay trên dữ liệu thử; tuyệt đối không dùng cho dữ liệu thật.'

    def add_arguments(self, parser):
        parser.add_argument('code', help='Mã STP trên màn hình QR thử')

    def handle(self, *args, **options):
        if not ready() or settings.SEPAY_MODE!='test':
            raise CommandError('Chỉ chạy khi SePay đã cấu hình và SEPAY_MODE=test. Không hỗ trợ live.')
        intent=SePayIntent.objects.filter(code=options['code'],mode='test',state='pending').first()
        if not intent or intent.expires_at<=timezone.now():
            raise CommandError('Không có phiên thử đang chờ còn hạn với mã này.')
        payload={'id':int(uuid.uuid4().int%10**18)+1,'gateway':intent.gateway,
                 'accountNumber':intent.account_number,'transferType':'in',
                 'transferAmount':int(intent.amount),'code':intent.code,
                 'content':'SIMULATION '+intent.code,'referenceCode':'LOCAL-TEST',
                 'transactionDate':timezone.now().astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')}
        raw=json.dumps(payload).encode();stamp=str(int(timezone.now().timestamp()))
        signature='sha256='+hmac.new(settings.SEPAY_WEBHOOK_SECRET.encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        request=RequestFactory().post('/api/sepay/webhook/',raw,content_type='application/json',
                                    HTTP_X_SEPAY_TIMESTAMP=stamp,HTTP_X_SEPAY_SIGNATURE=signature)
        response=webhook(request);result=json.loads(response.content)
        if response.status_code!=200 or result.get('state')!='applied':
            raise CommandError('Chưa ghi nhận thanh toán thử: '+json.dumps(result,ensure_ascii=False))
        self.stdout.write(self.style.SUCCESS('Đã ghi nhận giao dịch TEST cho '+intent.booking_code+'. Không có giao dịch ngân hàng thật.'))
