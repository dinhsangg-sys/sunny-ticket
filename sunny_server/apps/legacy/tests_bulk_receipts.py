import copy
import json
import uuid
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from apps.audit.models import AuditLog
from .models import Workspace

class BulkReceiptTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('bulk',password='test-password');self.client.force_login(self.user)
        self.data={'agents':[{'id':'a','name':'Nhân'},{'id':'b','name':'Tuyết'}],'bookings':[
            {'id':'one','bookingCode':'ONE','customerType':'agent','agent':'Nhân','revenue':100,'payments':[{'amount':20,'date':'2026-10-01'}]},
            {'id':'two','customerType':'agent','agentId':'a','agent':'Nhân','revenue':200,'payments':[]},
            {'id':'other','customerType':'agent','agent':'Tuyết','note':'Nhân','revenue':300,'payments':[]},
            {'id':'paid','customerType':'agent','agent':'Nhân','revenue':100,'payments':[{'amount':100}]},
            {'id':'retail1','customerType':'retail','customerName':'Nhân','revenue':100},
            {'id':'retail2','customerType':'retail','customerName':'Nhân','revenue':100}]}
        Workspace.objects.create(pk=1,data=copy.deepcopy(self.data))
        self.body={'revision':0,'action':'preview','party':'agent:a','ids':['one','two'],'date':'2026-10-27','note':'Chuyển khoản','batchId':str(uuid.uuid4())}

    def post(self,**changes):return self.client.post('/api/bulk-receipts/',json.dumps({**self.body,**changes}),content_type='application/json')

    def test_get_preview_and_apply_balances_once(self):
        listing=self.client.get('/api/bulk-receipts/');self.assertEqual(listing.status_code,200)
        groups={p['id']:p for p in listing.json()['parties']}
        self.assertEqual([b['id'] for b in groups['agent:a']['rows']],['one','two'])
        self.assertIn('booking:retail1',groups);self.assertIn('booking:retail2',groups)
        self.assertNotIn('buyPrice',str(listing.json()))
        preview=self.post();self.assertEqual(preview.status_code,200);self.assertEqual(preview.json()['total'],280)
        self.assertEqual(Workspace.objects.get(pk=1).revision,0)
        result=self.post(action='apply');self.assertEqual(result.status_code,200,result.content)
        current=Workspace.objects.get(pk=1);self.assertEqual(current.revision,1)
        one,two,other=current.data['bookings'][:3]
        self.assertEqual([p['amount'] for p in one['payments']],[20,80]);self.assertEqual(two['payments'][0]['amount'],200);self.assertEqual(other['payments'],[])
        self.assertEqual(one['payments'][-1]['batchId'],self.body['batchId'])
        self.assertEqual(AuditLog.objects.get().action,'receipt.bulk_create')
        duplicate=self.post(action='apply');self.assertTrue(duplicate.json()['duplicate']);self.assertEqual(Workspace.objects.get(pk=1).revision,1)
        self.assertEqual(self.post(action='apply',note='Khác').status_code,400)

    def test_invalid_or_mixed_selection_is_atomic(self):
        for ids in [['one','other'],['one','missing'],['one','one'],['paid'],['retail1','retail2'],[]]:
            with self.subTest(ids=ids):self.assertEqual(self.post(action='apply',ids=ids).status_code,400)
        for changes in [{'date':'bad'},{'date':None},{'batchId':'bad'},{'note':['invalid']}]:self.assertEqual(self.post(action='apply',**changes).status_code,400)
        self.assertEqual(Workspace.objects.get(pk=1).data,self.data);self.assertFalse(AuditLog.objects.exists())

    def test_revision_changed_after_preview_rejected(self):
        self.assertEqual(self.post().status_code,200)
        fresh=copy.deepcopy(self.data);fresh['bookings'][0]['payments'].append({'amount':10});Workspace.objects.filter(pk=1).update(data=fresh,revision=1)
        self.assertEqual(self.post(action='apply').status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).data,fresh)

    def test_ambiguous_name_not_grouped(self):
        fresh=copy.deepcopy(self.data);fresh['agents'].append({'id':'duplicate','name':'Nhân'});Workspace.objects.filter(pk=1).update(data=fresh)
        response=self.client.get('/api/bulk-receipts/').json();self.assertEqual(response['unresolved'],1)
        group=next(p for p in response['parties'] if p['id']=='agent:a');self.assertEqual([b['id'] for b in group['rows']],['two'])
        self.assertEqual(self.post(action='apply').status_code,400)

    def test_permissions(self):
        user=User.objects.create_user('limited',password='test-password',role='operator');self.client.force_login(user)
        self.assertEqual(self.client.get('/api/bulk-receipts/').status_code,403)
        for name in ['booking__view','receipt__view']:
            user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename=name))
        self.assertEqual(self.post().status_code,403)
        user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='receipt__create'))
        self.assertEqual(self.post(action='apply').status_code,200)
