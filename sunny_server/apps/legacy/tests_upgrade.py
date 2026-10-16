import copy
import json
from django.test import TestCase,Client
from django.contrib.auth.models import Permission,Group
from apps.accounts.models import User
from .models import Workspace
from .pricing import sell_price,supplier_options,validate,valid_zalo_link,choose_cost

def fixture():
    return {'ticketTypes':[{'id':'eco','name':'Eco','active':True},{'id':'eco-ah','name':'Eco An Huy','active':True},{'id':'eco-hbm','name':'Eco HBM','active':True}],
      'agents':[{'id':'a','name':'Đại lý A','priceListId':'standard'}],
      'suppliers':[{'id':'ah','name':'An Huy'},{'id':'hbm','name':'HBM'}],
      'priceLists':[{'id':'standard','name':'Chuẩn'}],
      'priceListItems':[{'id':'p1','priceListId':'standard','ticketId':'eco','price':450000,'from':'2026-01-01','to':''}],
      'costPrices':[{'ticketId':'eco','supplierId':'ah','price':350000,'from':'2026-01-01'},{'ticketId':'eco','supplierId':'hbm','price':370000,'from':'2026-01-01'}],
      'bookings':[{'id':'old','bookingCode':'OLD','date':'2026-01-01','ticketId':'eco-ah','ticketType':'Eco An Huy','qty':2,'sellPrice':430000,'buyPrice':320000,'cost':0,'revenue':860000,'profit':220000,'payments':[{'amount':100000}],'supplierPayments':[]}],
      'agentPrices':[],'expenses':[],'cashTransactions':[],'zaloCampaigns':[]}

class PricingRulesTests(TestCase):
    def test_same_supplier_overlapping_cost_tiers_are_allowed(self):
        data=fixture()
        data['costPrices'].append({'id':'tier-2','ticketId':'eco','supplierId':'ah','price':360000,'from':'2026-01-01','isDefault':True})
        validate(data)
        self.assertEqual(len([p for p in supplier_options(data,'eco','2026-10-16') if p['supplierId']=='ah']),2)
        self.assertEqual(choose_cost(data,'eco','ah','2026-10-16')['price'],360000)
        self.assertEqual(choose_cost(data,'eco','ah','2026-10-16','cost-row-0')['price'],350000)

    def test_selected_cost_tier_must_match_supplier_and_date(self):
        data=fixture()
        with self.assertRaises(ValueError):choose_cost(data,'eco','ah','2026-10-16','cost-row-1')
        with self.assertRaises(ValueError):choose_cost(data,'eco','ah','2025-01-01','cost-row-0')
    def test_common_sale_price_independent_of_source(self):
        data=fixture()
        self.assertEqual(sell_price(data,'a','eco','2026-10-16')[0],450000)
        self.assertEqual({p['price'] for p in supplier_options(data,'eco','2026-10-16')},{350000,370000})
    def test_agent_override_and_expiry(self):
        data=fixture();data['agentPrices']=[{'agent':'Đại lý A','ticketId':'eco','price':440000,'from':'2026-10-01','to':'2026-10-31'}]
        self.assertEqual(sell_price(data,'a','eco','2026-10-16')[0],440000)
        self.assertEqual(sell_price(data,'a','eco','2026-11-01')[0],450000)
    def test_no_price_is_not_zero(self):
        data=fixture();data['agents'][0]['priceListId']=''
        self.assertIsNone(sell_price(data,'a','eco','2026-10-16')[0])
    def test_equal_cost_suppliers_not_deduplicated(self):
        data=fixture();data['costPrices'][1]['price']=350000
        self.assertEqual(len(supplier_options(data,'eco','2026-10-16')),2)
    def test_zalo_link_host_validation(self):
        self.assertTrue(valid_zalo_link('https://zalo.me/0901234567'))
        for link in ['javascript:alert(1)','https://zalo.me.evil.com/1','https://zalo.me@evil.com/1','https://evil.com/1','http://zalo.me/1','https://zalo.me:444/1']:
            self.assertFalse(valid_zalo_link(link))

class RestrictedAccessTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('limited',role='operator')
        Workspace.objects.create(pk=1,data=fixture())
        self.client.force_login(self.user)
    def grant(self,*names):
        for name in names:self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename=name.replace('.','__')))
    def post(self,body):
        return self.client.post('/api/operations/',json.dumps({'revision':Workspace.objects.get(pk=1).revision,**body}),content_type='application/json')
    def test_role_does_not_grant_full_snapshot(self):
        self.assertEqual(self.client.get('/api/state/').status_code,403)
        self.assertEqual(self.client.put('/api/state/','{}',content_type='application/json').status_code,403)
    def test_no_permissions_no_resources(self):
        self.assertEqual(self.client.get('/api/operations/').json()['resources'],{})
    def test_view_only_cannot_modify(self):
        self.grant('ticket_type.view')
        self.assertEqual(self.post({'action':'create','resource':'ticketTypes','values':{'id':'fake','name':'Fake'}}).status_code,403)
    def test_direct_and_group_permission(self):
        group=Group.objects.create(name='Booking readers')
        group.permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='booking__view'))
        self.user.groups.add(group)
        data=self.client.get('/api/operations/').json()
        row=data['resources']['bookings']['rows'][0]
        for field in ('buyPrice','profit','payments','supplierPayments'):self.assertNotIn(field,row)
        self.assertEqual(row['revenue'],860000)
        self.user.groups.clear()
        self.assertNotIn('bookings',self.client.get('/api/operations/').json()['resources'])
    def test_booking_create_server_quotes_and_calculates(self):
        self.grant('booking.view','booking.create')
        result=self.post({'action':'create','resource':'bookings','values':{'date':'2026-10-16','customerType':'agent','agent':'Đại lý A','ticketId':'eco','supplierId':'hbm','qty':2}})
        self.assertEqual(result.status_code,200,result.content)
        row=Workspace.objects.get(pk=1).data['bookings'][-1]
        self.assertEqual(row['sellPrice'],450000)
        self.assertEqual(row['buyPrice'],370000)
        self.assertEqual(row['profit'],160000)

    def test_create_default_and_explicit_cost_tier(self):
        data=fixture()
        data['costPrices'].append({'id':'tier-2','ticketId':'eco','supplierId':'ah','price':360000,'from':'2026-01-01','isDefault':True})
        Workspace.objects.filter(pk=1).update(data=data)
        self.grant('booking.view','booking.create','booking.view_buy_price','booking.change_buy_price')
        values={'date':'2026-10-16','customerType':'agent','agent':'Đại lý A','ticketId':'eco','supplierId':'ah','qty':1}
        self.assertEqual(self.post({'action':'create','resource':'bookings','values':values}).status_code,200)
        row=Workspace.objects.get(pk=1).data['bookings'][-1]
        self.assertEqual(row['buyPrice'],360000)
        self.assertEqual(row['costPriceId'],'tier-2')
        response=self.post({'action':'create','resource':'bookings','values':dict(values,costPriceId='cost-row-0')})
        self.assertEqual(response.status_code,200,response.content)
        rows=Workspace.objects.get(pk=1).data['bookings']
        self.assertEqual(rows[-1]['buyPrice'],350000)
        self.assertEqual(rows[-2]['buyPrice'],360000)
    def test_cannot_inject_hidden_cost_or_derived_fields(self):
        self.grant('booking.view','booking.create')
        base={'date':'2026-10-16','customerType':'agent','agent':'Đại lý A','ticketId':'eco','supplierId':'ah','qty':1}
        self.assertEqual(self.post({'action':'create','resource':'bookings','values':dict(base,buyPrice=1)}).status_code,403)
        self.assertEqual(self.post({'action':'create','resource':'bookings','values':dict(base,profit=1)}).status_code,400)
    def test_quote_hides_costs(self):
        self.grant('booking.create')
        result=self.client.get('/api/quote/',{'agency':'a','ticket':'eco','date':'2026-10-16'}).json()
        self.assertEqual(result['price'],450000)
        self.assertNotIn('price',result['options'][0])
    def test_source_change_cannot_reassign_paid_supplier(self):
        data=fixture();data['bookings'][0].update(supplierId='ah',supplierPayments=[{'amount':10}])
        Workspace.objects.filter(pk=1).update(data=data)
        self.grant('booking.view','booking.change')
        response=self.post({'action':'change','resource':'bookings','index':0,'values':{'supplierId':'hbm'}})
        self.assertEqual(response.status_code,400)
    def test_stale_revision_rejected(self):
        self.grant('ticket_type.view','ticket_type.create')
        body={'action':'create','resource':'ticketTypes','values':{'id':'new','name':'New'}}
        self.assertEqual(self.post(body).status_code,200)
        r=self.client.post('/api/operations/',json.dumps(dict(body,revision=0)),content_type='application/json')
        self.assertEqual(r.status_code,409)

    def test_non_superuser_cannot_grant_full_access_via_group(self):
        self.user.is_staff=True;self.user.save()
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='auth',codename='add_group'))
        full=Permission.objects.get(content_type__app_label='legacy',codename='workspace__full_access')
        response=self.client.post('/admin/auth/group/add/',{'name':'Escalation','permissions':[full.pk],'_save':'Save'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(Group.objects.filter(name='Escalation').exists())

    def test_new_supplier_booking_does_not_change_history(self):
        before=copy.deepcopy(Workspace.objects.get(pk=1).data['bookings'][0])
        self.grant('booking.view','booking.create')
        self.assertEqual(self.post({'action':'create','resource':'bookings','values':{'date':'2026-10-16','customerType':'agent','agent':'Đại lý A','ticketId':'eco','supplierId':'ah','qty':1}}).status_code,200)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0],before)
