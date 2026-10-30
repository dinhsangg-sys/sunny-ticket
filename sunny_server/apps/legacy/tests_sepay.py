import copy
from datetime import timedelta
import hashlib
import hmac
import json
from urllib.parse import urlparse, parse_qs
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import Permission
from django.utils import timezone
from apps.accounts.models import User
from .models import Workspace, SePayIntent, SePayTransaction
from . import tests_counter as fixtures

@override_settings(SEPAY_ENABLED=True,SEPAY_MODE='test',SEPAY_WEBHOOK_SECRET='test-only-webhook-secret-01234567890123456789',SEPAY_BANK_CODE='TestBank',SEPAY_GATEWAY='Test Bank',SEPAY_ACCOUNT_NUMBER='0123456789',SEPAY_ACCOUNT_NAME='SUNNY TEST',SEPAY_TTL_SECONDS=900)
class SePayTests(TestCase):
    setUp=fixtures.CounterTests.setUp
    post=fixtures.CounterTests.post

    def new_intent(self):
        booking=self.post().json()['booking']
        response=self.client.post('/api/counter/bookings/'+booking['id']+'/sepay/','{}',content_type='application/json')
        self.assertEqual(response.status_code,201,response.content)
        return booking,SePayIntent.objects.get(pk=response.json()['id']),response.json()

    def payload(self,intent,**values):
        data={'id':123,'gateway':'Test Bank','accountNumber':'0123456789','transferType':'in','transferAmount':1100000,'transactionDate':timezone.localtime(intent.created_at+timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),'code':intent.code,'content':'Thanh toan '+intent.code,'referenceCode':'REF-TEST'}
        return {**data,**values}

    def hook(self,payload,secret=None,stamp=None,raw=None):
        from django.conf import settings
        raw=raw or json.dumps(payload).encode();stamp=str(stamp or int(timezone.now().timestamp()))
        signature='sha256='+hmac.new((secret or settings.SEPAY_WEBHOOK_SECRET).encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/sepay/webhook/',raw,content_type='application/json',HTTP_X_SEPAY_TIMESTAMP=stamp,HTTP_X_SEPAY_SIGNATURE=signature)

    def test_intent_server_amount_reuse_and_test_qr_cannot_be_bank_payment(self):
        booking,intent,result=self.new_intent()
        self.assertEqual(intent.amount,1100000);self.assertEqual(len(intent.code),21);self.assertTrue(result['qrUrl'].startswith('data:image/png;base64,'))
        again=self.client.post('/api/counter/bookings/'+booking['id']+'/sepay/','{}',content_type='application/json');self.assertEqual(again.json()['id'],str(intent.pk));self.assertEqual(SePayIntent.objects.count(),1)
        self.assertEqual(self.client.post('/api/counter/bookings/'+booking['id']+'/sepay/','{"amount":1}',content_type='application/json').status_code,400)
        stored=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(stored['payments'],[]);self.assertEqual(stored['paymentMethod'],'bank_transfer')

    def test_valid_signature_applies_once_and_duplicate_transfer_requires_review(self):
        booking,intent,_=self.new_intent();payload=self.payload(intent)
        self.assertEqual(self.hook(payload).json()['state'],'applied')
        self.assertTrue(self.hook(payload).json()['duplicate'])
        self.assertEqual(self.hook(self.payload(intent,id=124)).json()['state'],'review')
        stored=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(len(stored['payments']),1)
        self.assertEqual(stored['payments'][0]['amount'],1100000);self.assertEqual(stored['payments'][0]['providerTransactionId'],'123');self.assertEqual(stored['counterPaymentConfirmedBy'],'SePay (TEST)')
        self.assertEqual(stored['counterVersion'],1);self.assertEqual(stored['status'],'completed')
        intent.refresh_from_db();self.assertEqual(intent.state,'paid')

    def test_unsigned_tampered_stale_or_wrong_secret_never_writes(self):
        _,intent,_=self.new_intent();data=self.payload(intent)
        self.assertEqual(self.client.post('/api/sepay/webhook/',json.dumps(data),content_type='application/json').status_code,401)
        self.assertEqual(self.hook(data,secret='wrong').status_code,401)
        self.assertEqual(self.hook(data,stamp=int(timezone.now().timestamp())-301).status_code,401)
        raw=json.dumps(data).encode();stamp=str(int(timezone.now().timestamp()))
        from django.conf import settings
        sig='sha256='+hmac.new(settings.SEPAY_WEBHOOK_SECRET.encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        self.assertEqual(self.client.post('/api/sepay/webhook/',raw+b' ',content_type='application/json',HTTP_X_SEPAY_TIMESTAMP=stamp,HTTP_X_SEPAY_SIGNATURE=sig).status_code,401)
        self.assertEqual(SePayTransaction.objects.count(),0);self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'],[])

    def test_wrong_bank_account_amount_ambiguous_code_and_outgoing_are_not_applied(self):
        _,intent,_=self.new_intent()
        cases=[{'gateway':'OtherBank'},{'accountNumber':'9999999'},{'transferAmount':1},{'transferAmount':1100001},{'transferType':'out'},{'content':intent.code+' STP111111111111111111'},{'code':None,'content':'Khong co ma'}]
        for i,values in enumerate(cases):
            response=self.hook(self.payload(intent,id=200+i,**values));self.assertEqual(response.status_code,200,response.content);self.assertNotEqual(response.json()['state'],'applied')
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'],[])
        self.assertEqual(self.hook(self.payload(intent,id=0)).json()['ignored'],'provider_test_message')

    def test_cancel_or_edit_blocks_old_qr_and_prevents_manual_double_receipt(self):
        booking,intent,_=self.new_intent();key=booking['id']
        confirm=lambda:self.client.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps({'version':1,'paymentMethod':'cash','confirmed':True}),content_type='application/json')
        self.assertEqual(confirm().status_code,400)
        result=self.client.post('/api/counter/sepay/intents/'+str(intent.pk)+'/',json.dumps({'action':'cancel'}),content_type='application/json');self.assertEqual(result.status_code,200)
        self.assertEqual(confirm().status_code,200)
        self.assertEqual(self.hook(self.payload(intent)).json()['state'],'review')
        self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings'][0]['payments']),1)

    def test_booking_edit_invalidates_session_and_late_webhook_is_retained_for_review(self):
        booking,intent,_=self.new_intent()
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='counter__change'))
        response=self.client.post('/api/counter/bookings/'+booking['id']+'/',json.dumps({'version':1,'values':{'qty':3}}),content_type='application/json');self.assertEqual(response.status_code,200,response.content)
        intent.refresh_from_db();self.assertEqual(intent.state,'cancelled');self.assertEqual(self.hook(self.payload(intent)).json()['state'],'review')
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'],[])

    def test_expiry_uses_bank_transaction_time_and_does_not_credit_late_payment(self):
        _,intent,result=self.new_intent()
        old=timezone.now()-timedelta(minutes=20)
        SePayIntent.objects.filter(pk=intent.pk).update(created_at=old,expires_at=old+timedelta(minutes=15));intent.refresh_from_db()
        self.assertEqual(self.hook(self.payload(intent,transactionDate=timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'))).json()['state'],'review')
        # A delayed webhook for an actual payment inside its unchanged original window may settle.
        payload=self.payload(intent,id=125,transactionDate=timezone.localtime(old+timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(self.hook(payload).json()['state'],'applied')

    def test_customer_token_is_readonly_minimal_and_staff_access_is_owned(self):
        booking,intent,result=self.new_intent();token=result['displayUrl'].split('#')[1]
        anonymous=Client();response=anonymous.get('/api/sepay/display/',HTTP_AUTHORIZATION='Bearer '+token);self.assertEqual(response.status_code,200)
        for hidden in ('buyPrice','customerEmail','counterSellerId','WEBHOOK_SECRET','test-only-webhook-secret'):self.assertNotIn(hidden,response.content.decode())
        self.assertEqual(anonymous.get('/api/sepay/display/',HTTP_AUTHORIZATION='Bearer '+token+'x').status_code,404)
        self.assertEqual(anonymous.post('/api/sepay/display/',HTTP_AUTHORIZATION='Bearer '+token).status_code,405)
        other=User.objects.create_user('sepay-other',role='counter');other.user_permissions.add(*self.user.user_permissions.all());self.client.force_login(other)
        self.assertEqual(self.client.get('/api/counter/sepay/intents/'+str(intent.pk)+'/').status_code,404)
        self.assertEqual(self.client.post('/api/counter/bookings/'+booking['id']+'/sepay/','{}',content_type='application/json').status_code,404)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post('/api/counter/bookings/'+booking['id']+'/sepay/','{}',content_type='application/json').status_code,403)

    def test_disabled_configuration_and_live_qr_parameters(self):
        with override_settings(SEPAY_MODE='live'):
            _,intent,result=self.new_intent();query=parse_qs(urlparse(result['qrUrl']).query)
            self.assertEqual(urlparse(result['qrUrl']).hostname,'vietqr.app');self.assertEqual(query['amount'],['1100000']);self.assertEqual(query['des'],[intent.code]);self.assertEqual(query['acc'],['0123456789'])
        with override_settings(SEPAY_ENABLED=False):
            self.assertEqual(self.client.post('/api/counter/bookings/'+intent.booking_id+'/sepay/','{}',content_type='application/json').status_code,503)
            self.assertEqual(self.hook(self.payload(intent)).status_code,503)
            self.assertEqual(self.client.get('/api/sepay/display/').status_code,503)

    def test_legacy_edit_without_version_change_is_not_credited(self):
        _,intent,_=self.new_intent()
        obj=Workspace.objects.get(pk=1);obj.data['bookings'][0]['note']='Changed outside counter';obj.save()
        self.assertEqual(self.hook(self.payload(intent)).json()['state'],'review')
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'],[])

    @override_settings(SEPAY_MODE='live',SEPAY_BANK_CODE='VietinBank',SEPAY_GATEWAY='VietinBank')
    def test_vietinbank_qr_display_and_webhook_use_same_prefixed_content(self):
        _,intent,result=self.new_intent()
        memo='SEVQR '+intent.code
        self.assertEqual(parse_qs(urlparse(result['qrUrl']).query)['des'],[memo])
        self.assertEqual(result['paymentContent'],memo)
        # Bank may prepend its reference; SePay may leave code empty.
        payload=self.payload(intent,gateway='VietinBank',code=None,content='CT DEN:484T26 TEST '+memo)
        self.assertEqual(self.hook(payload).json()['state'],'applied')
        self.assertTrue(self.hook(payload).json()['duplicate'])

    def test_bank_aliases_use_prefix_and_other_banks_keep_existing_content(self):
        from .sepay import payment_content
        _,intent,result=self.new_intent()
        self.assertEqual(result['paymentContent'],intent.code)
        for bank in ('VietinBank','ICB','970415','vietinbank'):
            intent.bank_code=bank
            self.assertEqual(payment_content(intent),'SEVQR '+intent.code)
        intent.bank_code='TestBank';intent.gateway='VietinBank'
        self.assertEqual(payment_content(intent),'SEVQR '+intent.code)

    def test_simulation_command_is_test_only(self):
        from io import StringIO
        from django.core.management import call_command, CommandError
        _,intent,_=self.new_intent()
        with override_settings(SEPAY_MODE='live'):
            with self.assertRaises(CommandError):call_command('simulate_sepay_payment',intent.code,stdout=StringIO())
        self.assertEqual(SePayTransaction.objects.count(),0)
        call_command('simulate_sepay_payment',intent.code,stdout=StringIO())
        intent.refresh_from_db();self.assertEqual(intent.state,'paid')
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['counterPaymentConfirmedBy'],'SePay (TEST)')
