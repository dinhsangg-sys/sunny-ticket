import copy,hashlib,hmac,json,uuid
from datetime import timedelta
from django.conf import settings
from django.test import TestCase,Client,override_settings
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.cache import cache
from apps.accounts.models import User
from apps.legacy.models import Workspace,SePayIntent,SePayTransaction,CounterTicketBatch
from .models import Service,Article,OnlinePrice,OnlineOrder
from .views import quote

@override_settings(ALLOWED_HOSTS=['testserver','sunnygovn.com','www.sunnygovn.com','sn.hoianmemorieslands.com'],ONLINE_CHECKOUT_ENABLED=True,ONLINE_PAYMENT_OWNER='online-admin',COUNTER_EMAIL_ENABLED=True,EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',DEFAULT_FROM_EMAIL='test@example.test',SEPAY_ENABLED=True,SEPAY_MODE='test',SEPAY_WEBHOOK_SECRET='test-only-online-secret-01234567890123456789',SEPAY_BANK_CODE='TestBank',SEPAY_GATEWAY='Test Bank',SEPAY_ACCOUNT_NUMBER='0123456789',SEPAY_ACCOUNT_NAME='SUNNY TEST',SEPAY_TTL_SECONDS=900)
class OnlineTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin=User.objects.create_superuser('online-admin',password='test-only-password',role='admin')
        self.staff=User.objects.create_user('online-staff',role='counter',password='test-only-password')
        self.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['counter__view','counter__create']))
        self.staff.user_permissions.add(Permission.objects.get(content_type__app_label='online',codename='process_orders'))
        self.data={'agents':[],'ticketTypes':[{'id':'eco','name':'Eco','product':'Hội An','active':True}], 'suppliers':[{'id':'s','name':'Private supplier','active':True}], 'costPrices':[{'id':'cost','ticketId':'eco','supplierId':'s','price':400000,'from':'2020-01-01','to':'','isDefault':True}],'bookings':[]}
        Workspace.objects.create(pk=1,data=copy.deepcopy(self.data))
        self.service=Service.objects.create(title='Hội An từ góc nhìn địa phương',slug='hoi-an',ticket_id='eco',summary='Khám phá Hội An',body='Điều kiện vé. <script>alert(1)</script>',published=True)
        OnlinePrice.objects.create(service=self.service,price=600000,starts_on=timezone.localdate())
        self.day=timezone.localdate()+timedelta(days=1)
        self.url='/services/hoi-an/book/'
        self.body={'request_id':str(uuid.uuid4()),'visit_date':self.day.isoformat(),'qty':2,'customer_name':'Khách Sunny','email':'guest@example.test','phone':'0901234567','agreed':'on'}
    def create_order(self,**changes):
        response=self.client.post(self.url,{**self.body,**changes})
        self.assertEqual(response.status_code,302,response.content)
        return OnlineOrder.objects.get(request_id=self.body['request_id'])
    def intent(self):
        order=self.create_order();self.assertEqual(self.client.post('/online/orders/'+str(order.pk)+'/').status_code,200)
        order.refresh_from_db();return order,order.intent
    def hook(self,intent,**changes):
        payload={'id':123,'gateway':'Test Bank','accountNumber':'0123456789','transferType':'in','transferAmount':1200000,'transactionDate':timezone.localtime(intent.created_at+timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),'content':intent.code,'referenceCode':'ONLINE-TEST'}
        raw=json.dumps({**payload,**changes}).encode();stamp=str(int(timezone.now().timestamp()))
        signature='sha256='+hmac.new(settings.SEPAY_WEBHOOK_SECRET.encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/sepay/webhook/',raw,content_type='application/json',HTTP_X_SEPAY_TIMESTAMP=stamp,HTTP_X_SEPAY_SIGNATURE=signature)
    def test_public_root_host_and_role_routing(self):
        self.assertContains(self.client.get('/',HTTP_HOST='sunnygovn.com'),'Mỗi chuyến đi')
        self.assertEqual(self.client.get('/',HTTP_HOST='sn.hoianmemorieslands.com').status_code,302)
        self.client.force_login(self.admin);self.assertContains(self.client.get('/',HTTP_HOST='sunnygovn.com'),'id="app"')
        self.client.force_login(self.staff);self.assertRedirects(self.client.get('/',HTTP_HOST='sunnygovn.com'),'/counter/',fetch_redirect_response=False)
        self.assertContains(self.client.get('/discover/'),'Mỗi chuyến đi')
    def test_published_content_only_escaped_private_state_denied(self):
        hidden=Service.objects.create(title='Draft',slug='draft',ticket_id='eco',summary='draft',body='draft')
        self.assertNotContains(self.client.get('/services/'),'Draft')
        self.assertEqual(self.client.get('/services/draft/').status_code,404)
        self.assertContains(self.client.get('/services/hoi-an/'),'&lt;script&gt;')
        self.assertNotContains(self.client.get('/services/hoi-an/'),'Private supplier')
        self.assertEqual(self.client.get('/api/state/').status_code,302)
        self.assertEqual(self.client.get('/online/staff/').status_code,302)
    def test_server_pricing_idempotency_snapshot_and_session_isolation(self):
        order=self.create_order(total=1,unit_price=1);self.assertEqual(order.total,1200000)
        OnlinePrice.objects.update(price=700000)
        self.assertEqual(self.client.post(self.url,self.body).status_code,302);self.assertEqual(OnlineOrder.objects.count(),1)
        self.assertEqual(order.snapshot['cost']['price'],400000)
        self.assertEqual(Client().get('/online/orders/'+str(order.pk)+'/').status_code,404)
        self.assertEqual(Client().get('/online/orders/'+str(order.pk)+'/status/').status_code,404)
        self.assertEqual(self.client.post(self.url,{**self.body,'qty':3}).status_code,200);self.assertEqual(OnlineOrder.objects.count(),1)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'],[])
    def test_invalid_checkout_ambiguous_prices_and_closed_gate(self):
        for changes in [{'qty':0},{'qty':21},{'email':'bad'},{'phone':'x'},{'visit_date':'2000-01-01'},{'agreed':''},{'website':'bot'}]:
            self.assertEqual(self.client.post(self.url,{**self.body,**changes}).status_code,200)
        self.assertFalse(OnlineOrder.objects.exists())
        with self.settings(ONLINE_CHECKOUT_ENABLED=False):self.assertContains(self.client.post(self.url,self.body),'tạm đóng')
        with self.settings(EMAIL_HOST='',EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'):self.assertContains(self.client.post(self.url,self.body),'tạm đóng')
        price=OnlinePrice(service=self.service,price=1,starts_on=timezone.localdate())
        with self.assertRaises(ValidationError):price.full_clean()
        price.save()
        with self.assertRaises(ValueError):quote(self.service,self.day)
    def test_signed_webhook_only_creates_one_booking_and_reports_actual_receipt(self):
        order,intent=self.intent();self.assertEqual(intent.amount,1200000)
        self.assertEqual(self.client.post('/api/sepay/webhook/','{}',content_type='application/json').status_code,401)
        self.assertEqual(self.hook(intent).json()['state'],'applied');self.assertTrue(self.hook(intent).json()['duplicate'])
        self.assertEqual(self.hook(intent,id=124).json()['state'],'review')
        row=Workspace.objects.get(pk=1).data['bookings'][0]
        self.assertEqual(row['salesChannel'],'online');self.assertEqual(row['revenue'],1200000);self.assertEqual(row['date'],self.day.isoformat());self.assertEqual(row['payments'][0]['method'],'bank_transfer')
        self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings']),1)
        self.assertEqual(self.client.get('/online/orders/'+str(order.pk)+'/status/').json()['state'],'paid')
        self.client.force_login(self.admin);report=self.client.get('/api/reports/payment-methods/',{'source':'tickets','method':'bank_transfer'}).json();self.assertEqual(report['totals']['amount'],1200000)
    def test_wrong_bank_amount_expired_and_disabled_mode_require_review(self):
        order,intent=self.intent()
        for i,values in enumerate([{'transferAmount':1},{'accountNumber':'999999'},{'gateway':'Wrong'},{'transactionDate':'2000-01-01 00:00:00'},{'transferType':'out'}],1):
            self.assertNotEqual(self.hook(intent,id=i,**values).json()['state'],'applied')
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'],[])
        self.assertEqual(self.client.get('/online/orders/'+str(order.pk)+'/status/').json()['state'],'pending')
    def test_claim_permissions_owner_isolation_and_sent_state(self):
        order,intent=self.intent();self.hook(intent);self.client.force_login(self.staff)
        self.assertContains(self.client.get('/online/staff/'),order.code)
        self.assertRedirects(self.client.post('/online/staff/',{'order':str(order.pk)}),'/counter/?online=ONLINE-'+str(order.pk),fetch_redirect_response=False)
        order.refresh_from_db();self.assertEqual(order.assigned_to,self.staff)
        row=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(row['counterSellerId'],self.staff.pk)
        self.assertEqual(self.client.get('/api/counter/'+row['id']+'/tickets/').status_code,200)
        other=User.objects.create_user('no-permission',role='counter');self.client.force_login(other)
        self.assertEqual(self.client.get('/online/staff/').status_code,403)
        self.assertEqual(self.client.get('/api/counter/'+row['id']+'/tickets/').status_code,403)
        CounterTicketBatch.objects.create(owner=self.staff,booking_id=row['id'],source_name='ticket.pdf',source_hash='x',rows=[],email_state='sent',customer_email=order.email,emailed_at=timezone.now())
        from .views import order_state
        self.assertEqual(order_state(order)[0],'sent')
    def test_post_csrf_and_no_public_payment_override(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.url,self.body).status_code,403)
        order,intent=self.intent();self.assertEqual(self.client.post('/online/orders/'+str(order.pk)+'/status/',{'status':'paid'}).status_code,405)
        self.assertContains(self.client.get('/online/orders/'+str(order.pk)+'/'),'MÔI TRƯỜNG TEST')
    def test_order_hold_and_rate_limit(self):
        order=self.create_order();OnlineOrder.objects.filter(pk=order.pk).update(created_at=timezone.now()-timedelta(minutes=31))
        self.assertContains(self.client.post('/online/orders/'+str(order.pk)+'/'),'30 phút')
        self.assertEqual(SePayIntent.objects.count(),0)
        for i in range(9):
            self.body['request_id']=str(uuid.uuid4());self.create_order()
        self.body['request_id']=str(uuid.uuid4());self.assertContains(self.client.post(self.url,self.body),'nhiều yêu cầu')

    def test_staff_email_uses_existing_ticket_flow_and_records_sent(self):
        from unittest.mock import patch
        from django.core import mail
        order,intent=self.intent();self.hook(intent)
        self.client.force_login(self.staff);self.client.post('/online/staff/',{'order':str(order.pk)});order.refresh_from_db()
        batch=CounterTicketBatch.objects.create(owner=self.staff,booking_id=order.booking_id,source_name='tickets.pdf',source_hash='mail-test',rows=[],output_hash='verified-test-output')
        with patch('apps.legacy.counter_tickets.output_bytes',return_value=b'%PDF-test-only'):
            response=self.client.post('/api/counter/ticket-batches/'+str(batch.pk)+'/email/',json.dumps({'email':order.email,'confirmed':True}),content_type='application/json')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(len(mail.outbox),1);self.assertEqual(mail.outbox[0].to,[order.email]);self.assertTrue(mail.outbox[0].attachments)
        from .views import order_state
        self.assertEqual(order_state(order)[0],'sent')
    def test_primary_host_not_hijacked_by_souvenir_public_router(self):
        with self.settings(SOUVENIRS_ENABLED=True,SOUVENIRS_PUBLIC_ORIGIN='https://sunnygovn.com'):
            self.assertContains(self.client.get('/',HTTP_HOST='sunnygovn.com'),'Mỗi chuyến đi')
            self.assertEqual(self.client.get('/login/',HTTP_HOST='sunnygovn.com').status_code,200)

    def test_online_payment_and_amount_cannot_be_rewritten_by_workspace_editor(self):
        from apps.legacy.card_fees import protect_card_receipts
        order,intent=self.intent();self.hook(intent)
        before=Workspace.objects.get(pk=1).data
        for field,value in [('sellPrice',1),('qty',20),('salesChannel',''),('payments',[]),('customerEmail','someone@example.test')]:
            after=copy.deepcopy(before);after['bookings'][0][field]=value
            with self.assertRaises(ValueError):protect_card_receipts(before,after)
        after=copy.deepcopy(before);after['bookings'][0]['note']='Ghi chú xử lý'
        protect_card_receipts(before,after)
