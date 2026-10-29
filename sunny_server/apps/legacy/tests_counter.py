import copy
import json
import uuid
from datetime import datetime, timezone as utc
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace

class CounterTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('counter-one',password='test-password',role='counter')
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['counter__view','counter__create']))
        self.client.force_login(self.user)
        self.data={'agents':[],'ticketTypes':[{'id':'eco','name':'Eco','product':'Hội An','active':True}],'suppliers':[{'id':'s','name':'Nguồn bí mật','active':True}],
                   'costPrices':[{'id':'cost','ticketId':'eco','supplierId':'s','price':400000,'from':'2026-01-01','to':'','isDefault':True}],'bookings':[]}
        Workspace.objects.create(pk=1,data=copy.deepcopy(self.data))
        self.body={'requestId':str(uuid.uuid4()),'ticketId':'eco','qty':2,'sellPrice':550000,'hasVat':True,'note':'Khách tại quầy'}

    def post(self,body=None):return self.client.post('/api/counter/',json.dumps(body or self.body),content_type='application/json')

    @patch('django.utils.timezone.now',return_value=datetime(2026,10,28,18,30,tzinfo=utc.utc))
    def test_server_date_seller_defaults_vat_and_safe_response(self,_):
        self.assertRedirects(self.client.get('/'),'/counter/',fetch_redirect_response=False)
        response=self.post();self.assertEqual(response.status_code,201,response.content)
        row=Workspace.objects.get(pk=1).data['bookings'][0]
        self.assertEqual(row['date'],'2026-10-29');self.assertEqual(row['agent'],'counter-one');self.assertEqual(row['customerName'],'counter-one');self.assertEqual(row['customerType'],'retail')
        self.assertEqual(row['buyPrice'],400000);self.assertEqual(row['revenue'],1100000);self.assertEqual(row['vatRate'],15);self.assertEqual(row['vatAmount'],45000);self.assertEqual(row['payments'],[])
        self.assertEqual(row['supplierId'],'s');self.assertTrue(Workspace.objects.get(pk=1).data['ticketTypes'][0]['hasActivity'])
        for source in [response,self.client.get('/api/counter/')]:
            for hidden in ['buyPrice','profit','vatAmount','vatBase','supplierId','costPriceId','Nguồn bí mật','400000']:
                self.assertNotIn(hidden,source.content.decode())

    def test_rejects_client_injection_and_bad_values(self):
        for key,value in [('date','2000-01-01'),('agent','someone'),('buyPrice',0),('supplierId','x'),('vatRate',1),('payments',[{'amount':1}]),('counterSellerId',999)]:
            self.assertEqual(self.post({**self.body,key:value}).status_code,400)
        for key,value in [('qty',0),('qty',1.5),('qty',10001),('sellPrice',-1),('sellPrice','NaN'),('hasVat','true'),('note',[]),('ticketId','missing')]:
            self.assertEqual(self.post({**self.body,key:value}).status_code,400)
        self.assertEqual(Workspace.objects.get(pk=1).revision,0)

    def test_idempotency_and_own_records(self):
        self.assertEqual(self.post().status_code,201)
        repeat=self.post();self.assertEqual(repeat.status_code,200);self.assertTrue(repeat.json()['duplicate']);self.assertEqual(Workspace.objects.get(pk=1).revision,1)
        self.assertEqual(self.post({**self.body,'sellPrice':600000}).status_code,400)
        other=User.objects.create_user('counter-two',password='test-password',role='counter');other.user_permissions.add(*self.user.user_permissions.all());self.client.force_login(other)
        self.assertEqual(self.client.get('/api/counter/').json()['bookings'],[])
        response=self.post();self.assertEqual(response.status_code,201)
        rows=Workspace.objects.get(pk=1).data['bookings'];self.assertNotEqual(rows[0]['bookingCode'],rows[1]['bookingCode'])

    def test_no_default_inactive_supplier_ticket_and_ambiguous_default(self):
        for change in ('no_default','supplier_inactive','ticket_inactive','ambiguous'):
            data=copy.deepcopy(self.data)
            if change=='no_default':data['costPrices'][0]['isDefault']=False
            elif change=='supplier_inactive':data['suppliers'][0]['active']=False
            elif change=='ticket_inactive':data['ticketTypes'][0]['active']=False
            else:data['costPrices'].append({**data['costPrices'][0],'id':'duplicate'})
            Workspace.objects.filter(pk=1).update(data=data)
            self.assertEqual(self.post().status_code,400)
        self.assertEqual(Workspace.objects.get(pk=1).revision,0)

    def test_permissions_and_other_apis_closed(self):
        for url in ['/api/state/','/api/operations/','/api/quote/','/api/bulk-receipts/','/api/bulk-supplier-payments/']:
            self.assertEqual(self.client.get(url).status_code,403,url)
        self.user.user_permissions.clear()
        self.assertEqual(self.client.get('/counter/').status_code,403);self.assertEqual(self.post().status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='counter__view'))
        self.assertEqual(self.client.get('/api/counter/').status_code,200);self.assertEqual(self.post().status_code,403)

    def test_post_requires_csrf_and_zero_price_allowed(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post('/api/counter/',json.dumps(self.body),content_type='application/json').status_code,403)
        self.assertEqual(self.post({**self.body,'sellPrice':0,'hasVat':False}).status_code,201)

    def test_concurrent_change_blocks_without_overwrite(self):
        original=copy.deepcopy(self.data)
        with patch('apps.legacy.counter.save_workspace',side_effect=RuntimeError('conflict')):
            self.assertEqual(self.post().status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).data,original)
