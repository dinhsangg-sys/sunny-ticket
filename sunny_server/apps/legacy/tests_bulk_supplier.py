import copy
import json
import uuid
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace

class SupplierBulkTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('supplier-bulk',password='test-password');self.client.force_login(self.user)
        self.data={'suppliers':[{'id':'a','name':'An Huy','active':False},{'id':'b','name':'HBM'}],'bookings':[
            {'id':'one','supplierId':'a','ticketType':'Eco','qty':2,'buyPrice':60,'supplierPayments':[{'amount':20}],'payments':[{'amount':1}]},
            {'id':'two','supplierId':'b','ticketType':'Eco','qty':2,'buyPrice':70,'supplierPayments':[]},
            {'id':'three','supplierId':'a','ticketType':'High','qty':1,'buyPrice':80,'supplierPayments':[]},
            {'id':'manual1','costSource':'manual','supplierId':'__manual__','supplierName':'Nhân','qty':1,'buyPrice':20},
            {'id':'manual2','costSource':'manual','supplierId':'__manual__','supplierName':'Khác','qty':1,'buyPrice':30},
            {'id':'unknown','qty':1,'buyPrice':10}]}
        Workspace.objects.create(pk=1,data=copy.deepcopy(self.data));self.body={'action':'preview','revision':0,'party':'supplier:a','ids':['one','three'],'date':'2026-10-28','note':'Chi chuyển khoản','batchId':str(uuid.uuid4())}

    def post(self,**changes):return self.client.post('/api/bulk-supplier-payments/',json.dumps({**self.body,**changes}),content_type='application/json')

    def test_exact_saved_supplier_and_remaining_balance(self):
        listing=self.client.get('/api/bulk-supplier-payments/').json();groups={p['id']:p for p in listing['parties']};self.assertEqual(listing['unresolved'],1)
        self.assertEqual([r['id'] for r in groups['supplier:a']['rows']],['one','three']);self.assertIn('booking:manual1',groups);self.assertIn('booking:manual2',groups)
        self.assertEqual(self.post().json()['total'],180);self.assertEqual(Workspace.objects.get(pk=1).revision,0)
        result=self.post(action='apply');self.assertEqual(result.status_code,200,result.content)
        current=Workspace.objects.get(pk=1);self.assertEqual(current.data['bookings'][0]['supplierPayments'][-1]['amount'],100);self.assertEqual(current.data['bookings'][2]['supplierPayments'][-1]['amount'],80)
        self.assertEqual(current.data['bookings'][1]['supplierPayments'],[]);self.assertEqual(current.data['bookings'][0]['payments'],[{'amount':1}]);self.assertNotIn('cashTransactions',current.data)
        self.assertTrue(self.post(action='apply').json()['duplicate']);self.assertEqual(Workspace.objects.get(pk=1).revision,1)

    def test_mixed_supplier_or_manual_sources_cannot_be_paid_together(self):
        for changes in [{'ids':['one','two']},{'party':'booking:manual1','ids':['manual1','manual2']},{'ids':['one','unknown']},{'ids':['one','one']}]:self.assertEqual(self.post(action='apply',**changes).status_code,400)
        self.assertEqual(Workspace.objects.get(pk=1).data,self.data)

    def test_stale_revision_after_preview(self):
        self.assertEqual(self.post().status_code,200);Workspace.objects.filter(pk=1).update(revision=1)
        self.assertEqual(self.post(action='apply').status_code,409);self.assertEqual(Workspace.objects.get(pk=1).data,self.data)

    def test_requires_supplier_permissions_and_cost_visibility(self):
        user=User.objects.create_user('limited-supplier',password='test-password',role='operator');self.client.force_login(user)
        for name in ['booking__view','supplier_payment__view','supplier_payment__create']:user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename=name))
        self.assertEqual(self.post().status_code,403)
        user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='booking__view_buy_price'))
        self.assertEqual(self.post().status_code,200)
