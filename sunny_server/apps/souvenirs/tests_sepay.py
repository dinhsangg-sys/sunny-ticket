import json,hashlib,hmac
from datetime import timedelta
from django.conf import settings
from django.test import override_settings,Client,TestCase
from django.utils import timezone
from apps.legacy.models import SePayIntent,SePayTransaction,Workspace
from . import tests as fixtures
from .models import SaleOrder

@override_settings(SOUVENIRS_ENABLED=True,SOUVENIRS_PUBLIC_ORIGIN='https://souvenirs.test',ALLOWED_HOSTS=['testserver','souvenirs.test'],SEPAY_ENABLED=True,SEPAY_MODE='test',SEPAY_WEBHOOK_SECRET='test-only-souvenir-secret-01234567890123456789',SEPAY_BANK_CODE='TestBank',SEPAY_GATEWAY='Test Bank',SEPAY_ACCOUNT_NUMBER='0123456789',SEPAY_ACCOUNT_NAME='SUNNY TEST',SEPAY_TTL_SECONDS=900)
class SouvenirSePayTests(TestCase):
    setUp=fixtures.SouvenirsTests.setUp
    post=fixtures.SouvenirsTests.post
    create=fixtures.SouvenirsTests.create
    order=fixtures.SouvenirsTests.order
    action=fixtures.SouvenirsTests.action
    edit_body=fixtures.SouvenirsTests.edit_body
    def intent(self):
        order=self.order();url='/souvenirs/api/orders/'+order['id']+'/sepay/'
        response=self.client.post(url,'{}',content_type='application/json');self.assertEqual(response.status_code,201,response.content)
        return order,SePayIntent.objects.get(pk=response.json()['id']),response.json()
    def hook(self,intent,**overrides):
        payload={'id':123,'gateway':'Test Bank','accountNumber':'0123456789','transferType':'in','transferAmount':200000,'code':intent.code,'content':'Pay '+intent.code,'transactionDate':timezone.localtime(intent.created_at+timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),**overrides}
        raw=json.dumps(payload).encode();stamp=str(int(timezone.now().timestamp()));sig='sha256='+hmac.new(settings.SEPAY_WEBHOOK_SECRET.encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/sepay/webhook/',raw,content_type='application/json',HTTP_X_SEPAY_TIMESTAMP=stamp,HTTP_X_SEPAY_SIGNATURE=sig)
    def test_souvenir_qr_server_amount_display_signed_payment_once(self):
        order,intent,data=self.intent();self.assertEqual(intent.amount,200000);self.assertTrue(data['qrUrl'].startswith('data:image/png;base64,'));self.assertIn('/pay/sepay/#',data['displayUrl'])
        self.assertEqual(self.client.post('/souvenirs/api/orders/'+order['id']+'/sepay/','{}',content_type='application/json').json()['id'],str(intent.pk))
        self.assertEqual(Client().post('/api/sepay/webhook/','{}',content_type='application/json').status_code,401)
        self.assertEqual(self.hook(intent).json()['state'],'applied');self.assertTrue(self.hook(intent).json()['duplicate']);self.assertEqual(self.hook(intent,id=124).json()['state'],'review')
        obj=SaleOrder.objects.get(pk=order['id']);self.assertEqual(obj.status,'paid');self.assertEqual(obj.payment_method,'bank_transfer');self.assertEqual(obj.history[-1]['actor'],'SePay (TEST)')
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['id'],'TICKET-KEEP')
        self.client.force_login(self.admin);self.assertEqual(self.client.get('/souvenirs/api/report/').json()['totals']['total'],200000)
    def test_wrong_or_stale_souvenir_payments_need_review(self):
        order,intent,_=self.intent()
        for i,values in enumerate([{'transferAmount':1},{'accountNumber':'wrong'},{'gateway':'Other'},{'transferType':'out'},{'transactionDate':'2000-01-01 00:00:00'}]):
            self.assertNotEqual(self.hook(intent,id=200+i,**values).json()['state'],'applied')
        self.client.force_login(self.admin);self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order))
        intent.refresh_from_db();self.assertEqual(intent.state,'cancelled');self.assertEqual(self.hook(intent,id=300).json()['state'],'review')
        self.assertEqual(SaleOrder.objects.get(pk=order['id']).status,'pending')
    def test_sepay_cancel_manual_settle_delete_and_disabled_config(self):
        order,intent,_=self.intent();self.action(order,action='pay',method='cash',confirmed=True)
        intent.refresh_from_db();self.assertEqual(intent.state,'cancelled');self.assertEqual(self.hook(intent).json()['state'],'review')
        with self.settings(SEPAY_ENABLED=False):self.assertEqual(self.client.post('/souvenirs/api/orders/'+order['id']+'/sepay/','{}',content_type='application/json').status_code,503)
    def test_live_vietinbank_and_owner_scope(self):
        with self.settings(SEPAY_MODE='live',SEPAY_BANK_CODE='VietinBank',SEPAY_GATEWAY='VietinBank'):
            order,intent,data=self.intent();self.assertTrue(data['paymentContent'].startswith('SEVQR STP'));self.assertTrue(data['qrUrl'].startswith('https://vietqr.app/'))
        self.client.force_login(self.admin);self.action(order,action='delete',revision=0,confirmed=True,reason='Sai đơn')
        intent.refresh_from_db();self.assertEqual(intent.state,'cancelled')

    def test_souvenir_qr_permission_scope_and_stale_revision(self):
        from apps.accounts.models import User
        from django.contrib.auth.models import Permission
        order,intent,_=self.intent();url='/souvenirs/api/orders/'+order['id']+'/sepay/'
        other=User.objects.create_user('qr-other',role='counter');self.client.force_login(other)
        self.assertEqual(self.client.get(url).status_code,403)
        other.user_permissions.add(Permission.objects.get(content_type__app_label='souvenirs',codename='sell'))
        self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.admin)
        self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order))
        self.assertEqual(self.client.post(url,'{}',content_type='application/json').status_code,409)
        self.assertEqual(self.client.post(url,'{"revision":1}',content_type='application/json').status_code,201)
