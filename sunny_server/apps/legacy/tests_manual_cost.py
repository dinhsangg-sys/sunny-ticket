import json
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace

class ManualCostTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('root',password='test-password');self.client.force_login(self.user)
        self.data={'ticketTypes':[{'id':'eco','name':'Eco','active':True}],'agents':[{'id':'a','name':'Partner'}],'agentPrices':[{'agent':'Partner','ticketId':'eco','price':425000,'from':'2026-01-01'}],'suppliers':[],'bookings':[]}
        Workspace.objects.create(pk=1,data=self.data)
        self.values={'id':'manual','date':'2026-10-24','customerType':'agent','agent':'Partner','ticketId':'eco','qty':2,'costSource':'manual','buyPrice':350000,'manualSourceName':'Anh Nhân'}

    def operation(self,values):return self.client.post('/api/operations/',json.dumps({'revision':Workspace.objects.get(pk=1).revision,'action':'create','resource':'bookings','values':values}),content_type='application/json')

    def test_create_without_supplier_catalog_calculates_and_records_source(self):
        response=self.operation(self.values);self.assertEqual(response.status_code,200,response.content)
        b=Workspace.objects.get(pk=1).data['bookings'][0]
        self.assertEqual(b['buyPrice'],350000);self.assertEqual(b['sellPrice'],425000)
        self.assertEqual(b['profit'],150000);self.assertEqual(b['supplierId'],'__manual__');self.assertEqual(b['supplierName'],'Anh Nhân')
        self.assertEqual(b['costPriceId'],'')

    def test_zero_price_allowed_but_blank_negative_invalid_rejected(self):
        for value in ('',None,-1,'not-number'):
            self.assertEqual(self.operation(dict(self.values,buyPrice=value)).status_code,400)
        self.assertEqual(self.operation(dict(self.values,buyPrice=0)).status_code,200)

    def test_manual_source_requires_permission(self):
        self.user.is_superuser=False;self.user.role='operator';self.user.save()
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['booking__view','booking__create','booking__view_buy_price']))
        self.assertEqual(self.operation(self.values).status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='booking__change_buy_price'))
        self.assertEqual(self.operation(self.values).status_code,200)

    def test_full_snapshot_manual_booking_recomputed(self):
        data=dict(self.data,bookings=[dict(self.values,sellPrice=425000,revenue=1,profit=1)])
        response=self.client.put('/api/state/',json.dumps({'revision':0,'data':data}),content_type='application/json')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['profit'],150000)

    def test_cannot_rename_paid_manual_source(self):
        self.assertEqual(self.operation(self.values).status_code,200)
        obj=Workspace.objects.get(pk=1);data=obj.data;data['bookings'][0]['supplierPayments']=[{'amount':100000}];Workspace.objects.filter(pk=1).update(data=data)
        data['bookings'][0]['manualSourceName']='Other source'
        response=self.client.put('/api/state/',json.dumps({'revision':obj.revision,'data':data}),content_type='application/json')
        self.assertEqual(response.status_code,400)
