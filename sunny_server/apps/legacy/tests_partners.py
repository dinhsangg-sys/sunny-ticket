import copy
import json
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace
from .partners import partner_types,enforce_partner_types

class PartnerClassificationTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('root',password='test-password')
        self.client.force_login(self.user)
        self.data={'agents':[{'id':'a1','name':'Hotel A','priceListId':'standard'}],'priceLists':[{'id':'standard','name':'Chuẩn'}],'bookings':[{'id':'booking','agent':'Hotel A','revenue':100,'payments':[{'amount':50}]}]}
        Workspace.objects.create(pk=1,data=self.data)

    def put(self,data):return self.client.put('/api/state/',json.dumps({'data':data,'revision':Workspace.objects.get(pk=1).revision}),content_type='application/json')

    def test_existing_records_are_not_auto_classified(self):
        self.assertEqual(len(partner_types(self.data)),5)
        self.assertNotIn('partnerTypeId',Workspace.objects.get(pk=1).data['agents'][0])

    def test_classification_independent_of_price_and_history(self):
        data=copy.deepcopy(self.data);data['agents'][0]['partnerTypeId']='accommodation'
        self.assertEqual(self.put(data).status_code,200)
        stored=Workspace.objects.get(pk=1).data
        self.assertEqual(stored['agents'][0]['priceListId'],'standard')
        self.assertEqual(stored['bookings'],self.data['bookings'])

    def test_invalid_or_inactive_new_category_rejected(self):
        data=copy.deepcopy(self.data);data['partnerTypes']=partner_types({});data['partnerTypes'][0]['active']=False
        for key in ('missing','travel_agency'):
            data['agents'][0]['partnerTypeId']=key
            self.assertEqual(self.put(data).status_code,400)

    def test_suspend_category_retains_existing_assignment(self):
        before=copy.deepcopy(self.data);before['agents'][0]['partnerTypeId']='travel_agency'
        Workspace.objects.filter(pk=1).update(data=before)
        after=copy.deepcopy(before);after['partnerTypes']=partner_types({});after['partnerTypes'][0]['active']=False
        self.assertEqual(self.put(after).status_code,200)
        self.assertEqual(Workspace.objects.get(pk=1).data['agents'][0]['partnerTypeId'],'travel_agency')

    def test_used_category_cannot_be_removed(self):
        before=copy.deepcopy(self.data);before['agents'][0]['partnerTypeId']='accommodation';Workspace.objects.filter(pk=1).update(data=before)
        after=copy.deepcopy(before);after['partnerTypes']=[];after['agents']=[]
        self.assertEqual(self.put(after).status_code,400)

    def test_restricted_assignment_requires_specific_permission(self):
        self.user.is_superuser=False;self.user.role='operator';self.user.save()
        for code in ('agency__view','agency__change'):
            self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename=code))
        body={'revision':0,'action':'change','resource':'agents','index':0,'values':{'partnerTypeId':'tour_guide'}}
        response=self.client.post('/api/operations/',json.dumps(body),content_type='application/json')
        self.assertEqual(response.status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='agency__classify'))
        response=self.client.post('/api/operations/',json.dumps(body),content_type='application/json')
        self.assertEqual(response.status_code,200,response.content)

    def test_category_management_uses_defaults_and_permission(self):
        self.user.is_superuser=False;self.user.role='operator';self.user.save()
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['partner_type__view','partner_type__change']))
        response=self.client.get('/api/operations/').json()
        self.assertEqual(len(response['resources']['partnerTypes']['rows']),5)
        response=self.client.post('/api/operations/',json.dumps({'revision':0,'action':'change','resource':'partnerTypes','index':0,'values':{'name':'Đại lý bán vé'}}),content_type='application/json')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(Workspace.objects.get(pk=1).data['partnerTypes'][0]['name'],'Đại lý bán vé')
