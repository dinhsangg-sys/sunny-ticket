import copy
import json
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace

class CopyPriceTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('root',password='test-password')
        self.client.force_login(self.user)
        self.data={'agents':[{'id':'src','name':'Source','priceListId':'common'},{'id':'dst','name':'Target'}], 'ticketTypes':[{'id':'eco','name':'Eco','active':True},{'id':'vip','name':'VIP','active':True}], 'priceLists':[{'id':'common','name':'Common'}], 'priceListItems':[{'id':'shared','priceListId':'common','ticketId':'vip','price':500,'from':'2026-01-01'}], 'agentPrices':[{'id':'p1','agent':'Source','ticketId':'eco','ticketType':'Eco','price':400,'from':'2026-01-01'}], 'bookings':[{'id':'b1','agent':'Target','revenue':100,'buyPrice':60,'payments':[{'amount':20}]}]}
        Workspace.objects.create(pk=1,data=self.data)
        self.params={'source':'src','target':'dst','mode':'private','sourceDate':'2026-10-24','from':'2026-10-24','to':'','revision':0}

    def post(self,**kw):return self.client.post('/api/copy-prices/',json.dumps({**self.params,**kw}),content_type='application/json')

    def test_preview_has_no_side_effects(self):
        response=self.post(action='preview')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['rows'][0]['status'],'add')
        self.assertEqual(Workspace.objects.get(pk=1).data,self.data)

    def test_apply_preserves_source_history_and_target_assignment(self):
        self.assertEqual(self.post(action='apply',tickets=['eco']).status_code,200)
        stored=Workspace.objects.get(pk=1).data
        self.assertEqual(stored['agentPrices'][0],self.data['agentPrices'][0])
        self.assertEqual(stored['bookings'],self.data['bookings'])
        self.assertEqual(stored['agents'],self.data['agents'])
        copied=stored['agentPrices'][-1]
        self.assertEqual(copied['agent'],'Target');self.assertEqual(copied['price'],400)
        self.assertNotEqual(copied['id'],'p1')
        self.assertEqual(copied['from'],'2026-10-24')

    def test_destination_conflict_never_overwritten(self):
        data=copy.deepcopy(self.data);data['agentPrices'].append({'id':'dest','agent':'Target','ticketId':'eco','price':450,'from':'2026-10-01'})
        Workspace.objects.filter(pk=1).update(data=data)
        self.assertEqual(self.post(action='preview').json()['rows'][0]['status'],'conflict')
        self.assertEqual(self.post(action='apply',tickets=['eco']).json()['added'],0)
        self.assertEqual(Workspace.objects.get(pk=1).data,data)

    def test_duplicate_only_when_destination_fully_covers_requested_period(self):
        data=copy.deepcopy(self.data);data['agentPrices'].append({'agent':'Target','ticketId':'eco','price':400,'from':'2026-10-01','to':'2026-10-31'})
        Workspace.objects.filter(pk=1).update(data=data)
        self.assertEqual(self.post(action='preview',to='2026-10-30').json()['rows'][0]['status'],'duplicate')
        self.assertEqual(self.post(action='preview').json()['rows'][0]['status'],'conflict')

    def test_effective_price_mode_includes_shared_prices(self):
        rows=self.post(action='preview',mode='effective').json()['rows']
        self.assertEqual({r['ticketId'] for r in rows},{'eco','vip'})
        self.assertEqual(self.post(action='preview').json()['rows'][0]['ticketId'],'eco')

    def test_selected_tickets_only_and_stale_revision(self):
        self.assertEqual(self.post(action='apply',mode='effective',tickets=['vip']).status_code,200)
        rows=Workspace.objects.get(pk=1).data['agentPrices']
        self.assertEqual([p['ticketId'] for p in rows if p['agent']=='Target'],['vip'])
        self.assertEqual(self.post(action='apply',tickets=['eco']).status_code,409)

    def test_same_partner_invalid_dates_and_empty_selection(self):
        self.assertEqual(self.post(action='preview',target='src').status_code,400)
        self.assertEqual(self.post(action='preview',to='2026-01-01').status_code,400)
        self.assertEqual(self.post(action='apply',tickets=[]).status_code,400)

    def test_ambiguous_partner_name_is_rejected(self):
        data=copy.deepcopy(self.data);data['agents'].append({'id':'duplicate','name':'Source'})
        Workspace.objects.filter(pk=1).update(data=data)
        self.assertEqual(self.post(action='preview').status_code,400)

    def test_assign_shared_list_is_explicit_and_does_not_copy_rows(self):
        response=self.post(action='assign')
        self.assertEqual(response.status_code,200,response.content)
        stored=Workspace.objects.get(pk=1).data
        self.assertEqual(stored['agents'][1]['priceListId'],'common')
        self.assertEqual(stored['agentPrices'],self.data['agentPrices'])

    def test_restricted_permissions_checked_for_source_and_destination(self):
        self.user.is_superuser=False;self.user.role='operator';self.user.save()
        self.assertEqual(self.post(action='preview').status_code,403)
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['agency__view','agency_price__view']))
        self.assertEqual(self.post(action='preview').status_code,200)
        self.assertEqual(self.post(action='apply',tickets=['eco']).status_code,403)
        self.assertEqual(self.post(action='preview',mode='effective').status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='agency_price__create'))
        self.assertEqual(self.post(action='apply',tickets=['eco']).status_code,200)
