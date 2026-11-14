import copy,csv,json,uuid
from io import StringIO
from datetime import datetime,timezone as utc
from decimal import Decimal
from django.test import TestCase,override_settings
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from apps.souvenirs.models import SaleOrder
from .models import Workspace

@override_settings(SOUVENIRS_ENABLED=True)
class PaymentMethodReportTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('report-admin',password='test-only-password',role='admin');self.client.force_login(self.user)
        self.data={'agents':[],'bookings':[
            {'id':'B1','bookingCode':'ST-OLD-1','date':'2026-01-01','paymentMethod':'cash','agent':'=BAD()','payments':[
                {'id':'p1','date':'2026-11-02','amount':100000,'method':'cash'},
                {'id':'p2','date':'2026-11-03','amount':200000,'method':'bank_transfer'},
                {'id':'p3','date':'2026-11-03','amount':300000,'method':'card','cardFee':{'feeAmount':7500}},
                {'id':'p4','date':'2026-11-03','amount':40000,'note':'Chuyen khoan','method':''},
                {'id':'p5','amount':5000,'method':'cash'},
                {'id':'p6','createdAt':'2026-11-01T17:30:00Z','amount':6000,'provider':'sepay'},
                {'id':'p7','date':'2026-11-03','amount':7000,'method':'card'}]},
            {'id':'B2','bookingCode':'ST-NEW-2','date':'2026-11-03','agent':'Other','payments':[{'date':'2026-10-01','amount':999999,'method':'cash'}]},
            {'id':'B3','status':'cancelled','payments':[{'date':'2026-11-03','amount':888888,'method':'cash'}]},
            {'id':'B4','payments':[],'revenue':1000000}]}
        Workspace.objects.create(pk=1,data=copy.deepcopy(self.data))
    def report(self,**values):return self.client.get('/api/reports/payment-methods/',{'source':'tickets','from':'2026-11-02','to':'2026-11-03',**values})
    def order(self,**values):
        return SaleOrder.objects.create(request_id=uuid.uuid4(),fingerprint='test',seller=self.user,seller_name='Sunny',total=120000,cost_total=1000,status='paid',payment_method='bank_transfer',paid_at=datetime(2026,11,1,17,30,tzinfo=utc.utc),**values)
    def test_ticket_receipts_group_actual_date_split_methods_and_unknown(self):
        response=self.report();self.assertEqual(response.status_code,200,response.content);data=response.json();groups={g['method']:g for g in data['groups']}
        self.assertEqual(data['totals']['amount'],653000);self.assertEqual(data['totals']['fee'],7500);self.assertEqual(data['totals']['net'],645500)
        self.assertEqual(data['totals']['receipts'],6);self.assertEqual(data['totals']['orders'],1)
        self.assertEqual(groups['cash']['amount'],100000);self.assertEqual(groups['bank_transfer']['amount'],206000);self.assertEqual(groups['card']['amount'],307000);self.assertEqual(groups['unknown']['amount'],40000)
        self.assertEqual(data['warnings']['undatedCount'],1);self.assertEqual(data['warnings']['undatedAmount'],5000);self.assertEqual(data['warnings']['cardFeeMissingCount'],1)
        self.assertNotIn('cost',data['rows'][0]);self.assertNotIn('buyPrice',response.content.decode())
        filtered=self.report(method='bank_transfer').json();self.assertEqual(filtered['totals']['amount'],206000)
    def test_clear_dates_includes_old_undated_and_no_booking_date_guess(self):
        data=self.report(**{'from':'','to':''}).json();self.assertEqual(data['totals']['amount'],1657999)
        self.assertTrue(any(r['date']=='' and r['amount']==5000 for r in data['rows']))
        self.assertEqual(self.report(**{'from':'2026-01-01','to':'2026-01-01'}).json()['totals']['amount'],0)
    def test_souvenir_paid_date_hcm_deleted_pending_and_permissions(self):
        order=self.order();self.order(deleted_at=datetime.now(utc.utc));pending=self.order();pending.status='pending';pending.save()
        response=self.report(source='souvenirs',**{'from':'2026-11-02','to':'2026-11-02'});self.assertEqual(response.json()['totals']['amount'],120000)
        self.assertEqual(response.json()['rows'][0]['date'],'2026-11-02')
        order.total=Decimal(150000);order.save();self.assertEqual(self.report(source='souvenirs').json()['totals']['amount'],150000)
        viewer=User.objects.create_user('shop-viewer',role='counter');viewer.user_permissions.add(Permission.objects.get(content_type__app_label='souvenirs',codename='view_reports'));self.client.force_login(viewer)
        self.assertEqual(self.report(source='souvenirs').status_code,200);self.assertEqual(self.report().status_code,403)
    def test_ticket_permission_separate_from_sales_and_other_source(self):
        viewer=User.objects.create_user('receipt-viewer',role='operator');self.client.force_login(viewer)
        self.assertEqual(self.report().status_code,403)
        viewer.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['receipt__view','booking__view']))
        self.assertEqual(self.report().status_code,200);self.assertEqual(self.report(source='souvenirs').status_code,403)
        self.assertEqual(self.client.get('/reports/payment-methods/?source=tickets').status_code,200)
    def test_csv_same_filter_numeric_totals_utf8_and_formula_safety(self):
        response=self.report(format='csv',method='cash');self.assertEqual(response.status_code,200);self.assertIn('attachment',response['Content-Disposition'])
        rows=list(csv.reader(StringIO(response.content.decode('utf-8-sig'))));self.assertTrue(any("'=BAD()" in row for row in rows));self.assertTrue(any('100000.0' in row for row in rows));self.assertNotIn('200000.0',response.content.decode('utf-8-sig'))
        self.assertEqual(Workspace.objects.get(pk=1).data,self.data)
    def test_bad_dates_method_source_and_corrupt_data(self):
        for values in ({'from':'2026-11-04','to':'2026-11-01'},{'from':'2026-02-30'},{'method':'guess'},{'source':'all'},{'from':'20261102'}):self.assertEqual(self.report(**values).status_code,400)
        obj=Workspace.objects.get(pk=1);obj.data['bookings'][0]['payments'].append({'date':'2026-11-03','method':'cash','amount':'NaN'});obj.save()
        self.assertEqual(self.report().json()['warnings']['invalidCount'],1)
