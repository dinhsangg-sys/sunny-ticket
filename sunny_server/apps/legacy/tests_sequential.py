import json
from django.test import TestCase
from apps.accounts.models import User
from .models import Workspace

class SequentialSaveTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('sequential',password='test-password')
        self.client.force_login(self.user)

    def test_sequential_catalog_saves_return_canonical_data_and_revision(self):
        data={'agents':[],'ticketTypes':[],'suppliers':[],'costPrices':[],'agentPrices':[],'bookings':[],'expenses':[],'priceLists':[],'priceListItems':[]}
        revision=0
        for resource in ['agents','ticketTypes','suppliers','expenses','priceLists']:
            for i in range(3):
                data[resource].append({'id':resource+str(i),'name':'Tên '+str(i),'active':True})
                response=self.client.put('/api/state/',json.dumps({'revision':revision,'data':data}),content_type='application/json')
                self.assertEqual(response.status_code,200,response.content)
                payload=response.json();revision+=1
                self.assertEqual(payload['revision'],revision)
                self.assertEqual(payload['data'],Workspace.objects.get(pk=1).data)
                data=payload['data']
                self.assertIn('no-store',response['Cache-Control'])
        fresh=self.client.get('/api/state/')
        self.assertIn('no-store',fresh['Cache-Control'])
        self.assertEqual(fresh.json()['revision'],15)
        stale=self.client.put('/api/state/',json.dumps({'revision':0,'data':{}}),content_type='application/json')
        self.assertEqual(stale.status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).data,data)
