import copy,json,uuid
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.utils import timezone
from apps.accounts.models import User
from . import tests_counter as fixtures
from .models import Workspace,CardFeeRate,BookingCancellation,SePayIntent,CounterTicketBatch
from .card_fees import quote_fee,references

class BookingCancellationTests(TestCase):
    setUp=fixtures.CounterTests.setUp
    post=fixtures.CounterTests.post
    def grant(self):self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='booking__cancel_paid'))
    def create_paid(self,method='card'):
        self.row=self.post().json()['booking'];self.url='/api/bookings/'+self.row['id']+'/cancel/'
        body={'version':1,'paymentRevision':0,'paymentMethod':method,'confirmed':True}
        if method=='card':
            self.rate=CardFeeRate.objects.create(scheme='visa',origin='domestic',rate='2.55',starts_on=timezone.localdate());body['cardFeeQuote']=quote_fee('visa','domestic',1100000)
        response=self.client.post('/api/counter/bookings/'+self.row['id']+'/confirm-payment/',json.dumps(body),content_type='application/json');self.assertEqual(response.status_code,200,response.content)
        return self.row
    def cancel(self,**changes):
        preview=self.client.get(self.url);self.assertEqual(preview.status_code,200,preview.content)
        body={'token':preview.json()['token'],'reason':'Booking nhập nhầm','resolution':'mistake','reference':'','retainedFee':0,'confirmed':True,**changes}
        return self.client.post(self.url,json.dumps(body),content_type='application/json')
    def test_permission_scope_and_admin_default(self):
        self.create_paid();self.assertEqual(self.client.get(self.url).status_code,403);self.grant();self.assertEqual(self.client.get(self.url).status_code,200)
        other=User.objects.create_user('other-counter',role='counter');other.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='booking__cancel_paid'));self.client.force_login(other)
        self.assertEqual(self.client.get(self.url).status_code,404);self.assertEqual(self.client.get('/api/booking-cancellations/').json()['rows'],[])
        admin=User.objects.create_user('plain-admin',role='admin');self.client.force_login(admin);self.assertEqual(self.cancel().status_code,200)
        self.assertEqual(BookingCancellation.objects.count(),1)
    def test_card_cancellation_archives_fee_history_reserves_code_and_blocks_recreate(self):
        self.create_paid();self.grant();original=copy.deepcopy(Workspace.objects.get(pk=1).data['bookings'][0])
        batch=CounterTicketBatch.objects.create(owner=self.user,booking_id=self.row['id'],source_name='source.pdf',source_hash='test',rows=[],selected=[])
        response=self.cancel();self.assertEqual(response.status_code,200,response.content)
        archive=BookingCancellation.objects.get();self.assertEqual(archive.snapshot,original);self.assertEqual(references(self.rate.pk)[0]['feeAmount'],28050)
        data=Workspace.objects.get(pk=1).data;self.assertEqual(data['bookings'],[]);self.assertEqual(data['cashTransactions'] if 'cashTransactions' in data else [],[])
        self.assertTrue(CounterTicketBatch.objects.filter(pk=batch.pk).exists())
        self.assertEqual(self.client.get('/api/counter/').json()['bookings'],[])
        self.assertTrue(self.client.post(self.url,'{}',content_type='application/json').json()['duplicate']);self.assertEqual(BookingCancellation.objects.count(),1)
        self.assertEqual(self.post().status_code,400)
        new=self.post({**self.body,'requestId':str(uuid.uuid4())});self.assertEqual(new.status_code,201,new.content);self.assertNotEqual(new.json()['booking']['bookingCode'],original['bookingCode'])
        from .card_fees import protect_card_receipts
        with self.assertRaises(ValueError):protect_card_receipts(data,{**data,'bookings':[original]})
        with self.assertRaises(ValueError):protect_card_receipts(data,{**data,'cancelledBookingCodes':[]})
    def test_refunded_retained_fee_persists_as_cash_expense_once(self):
        self.create_paid();self.grant();response=self.cancel(resolution='refunded',reference='POS-VOID-123',retainedFee=10000)
        self.assertEqual(response.status_code,200,response.content);data=Workspace.objects.get(pk=1).data
        expense=data['cashTransactions'][0];self.assertEqual(expense['amount'],10000);self.assertEqual(expense['kind'],'expense');self.assertEqual(expense['date'],timezone.localdate().isoformat())
        self.client.post(self.url,'{}',content_type='application/json');self.assertEqual(len(Workspace.objects.get(pk=1).data['cashTransactions']),1)
        self.assertEqual(self.client.get('/api/booking-cancellations/').json()['rows'][0]['retainedFee'],10000)
    def test_bad_confirmation_reference_fees_and_concurrency_never_cancel(self):
        self.create_paid();self.grant()
        for changes in ({'reason':''},{'confirmed':False},{'retainedFee':99999},{'retainedFee':-1},{'resolution':'refunded','reference':''},{'retainedFee':1.5}):self.assertEqual(self.cancel(**changes).status_code,400)
        preview=self.client.get(self.url).json();obj=Workspace.objects.get(pk=1);obj.data['bookings'][0]['note']='Vừa thay đổi';obj.save()
        body={'token':preview['token'],'reason':'Booking nhập nhầm','resolution':'mistake','reference':'','retainedFee':0,'confirmed':True}
        self.assertEqual(self.client.post(self.url,json.dumps(body),content_type='application/json').status_code,409)
        self.assertEqual(BookingCancellation.objects.count(),0);self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings']),1)
    def test_live_sepay_receipt_requires_refund_reconciliation(self):
        self.create_paid(method='bank_transfer');self.grant();obj=Workspace.objects.get(pk=1);obj.data['bookings'][0]['payments'][0]['provider']='sepay';obj.save()
        self.assertEqual(self.cancel().status_code,400);self.assertEqual(self.cancel(resolution='refunded',reference='BANK-REFUND-123').status_code,200)
    def test_pending_qr_is_cancelled_and_ticket_access_closed(self):
        self.row=self.post().json()['booking'];self.url='/api/bookings/'+self.row['id']+'/cancel/';self.grant()
        intent=SePayIntent.objects.create(owner=self.user,booking_id=self.row['id'],booking_code=self.row['bookingCode'],booking_version=1,booking_fingerprint='x',code='STP000000000000000001',amount=1100000,bank_code='TEST',gateway='Test',account_number='1234',account_name='Test',expires_at=timezone.now())
        self.assertEqual(self.cancel().status_code,200);intent.refresh_from_db();self.assertEqual(intent.state,'cancelled')
        self.assertEqual(self.client.get('/api/counter/bookings/'+self.row['id']+'/').status_code,404)

    def test_supplier_costs_hidden_from_counter_and_admin_reconciliation_required(self):
        self.create_paid();self.grant();obj=Workspace.objects.get(pk=1);obj.data['bookings'][0]['supplierPayments']=[{'amount':800000,'date':timezone.localdate().isoformat()}];obj.save()
        preview=self.client.get(self.url).json();self.assertTrue(preview['hasSupplierPayments']);self.assertIsNone(preview['supplierPaid']);self.assertEqual(self.cancel().status_code,400)
        admin=User.objects.create_user('supplier-admin',role='admin');self.client.force_login(admin)
        self.assertEqual(self.client.get(self.url).json()['supplierPaid'],800000)
        self.assertEqual(self.cancel(resolution='refunded',reference='CUSTOMER-SUPPLIER-REFUND').status_code,200)
