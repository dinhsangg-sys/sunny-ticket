import copy,importlib
from django.apps import apps
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.legacy.models import Workspace
from apps.accounts.models import User
from .models import Service,ServiceTicketGroup,ServiceOption,OnlinePrice
from .views import quote
from .card_prices import attach_card_prices

class ManagementTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('manager',password='test-only')
        self.client.force_login(self.user)
        self.data={'ticketTypes':[{'id':'eco','name':'Eco NL','active':True}],'suppliers':[{'id':'s','name':'Supplier','active':True}], 'costPrices':[{'id':'c','ticketId':'eco','supplierId':'s','price':400000,'from':'2020-01-01','isDefault':True}]}
        Workspace.objects.create(pk=1,data=copy.deepcopy(self.data))
        self.service=Service.objects.create(title='Ký Ức',slug='ky-uc',summary='Intro',body='Story',published=True)
        self.group=ServiceTicketGroup.objects.create(service=self.service,name='ECO',name_en='ECO')
    def option(self,**values):
        return ServiceOption.objects.create(service=self.service,group=self.group,group_name='ECO',audience='adult',title='ECO adult',ticket_id='eco',online_price=540000,published_price=600000,**values)
    def test_admin_save_group_ticket_and_default_price(self):
        url=f'/admin/online/serviceticketgroup/{self.group.pk}/change/'
        response=self.client.get(url);self.assertContains(response,'Giá online mặc định')
        response=self.client.post(url,{'name':'ECO','name_en':'ECO','sort_order':'0','options-TOTAL_FORMS':'1','options-INITIAL_FORMS':'0','options-MIN_NUM_FORMS':'0','options-MAX_NUM_FORMS':'1000','options-0-ticket_id':'eco','options-0-audience':'adult','options-0-published_price':'600000','options-0-online_price':'540000','options-0-strike_published_price':'on','options-0-active':'on','options-0-sort_order':'0','_save':'Lưu'})
        self.assertEqual(response.status_code,302,str(response.context and response.context.get('inline_admin_formsets')))
        option=self.service.options.get();self.assertEqual(option.online_price,540000);self.assertEqual(option.service_id,self.service.pk)
        self.assertEqual(quote(self.service,timezone.localdate(),option)[0],540000)
        self.assertRedirects(self.client.get(f'/services/{self.service.slug}/book/'),f'/services/{self.service.slug}/',fetch_redirect_response=False)
        with self.assertRaises(ValueError):quote(self.service,timezone.localdate())
    def test_default_overrides_old_periods_and_public_price(self):
        option=self.option(strike_published_price=True)
        OnlinePrice.objects.create(service=self.service,option=option,price=500000,starts_on=timezone.localdate())
        self.assertEqual(quote(self.service,timezone.localdate(),option)[0],540000)
        self.client.logout();response=self.client.get(f'/services/{self.service.slug}/prices/',{'date':str(timezone.localdate())})
        row=response.json()['options'][0];self.assertEqual(row['published_price'],600000);self.assertTrue(row['strike_published_price'])
        self.assertEqual(attach_card_prices([self.service])[0].card_price,540000)
        option.online_price=700000
        with self.assertRaises(ValidationError):option.full_clean()
        option.online_price=0
        with self.assertRaises(ValidationError):option.full_clean()
    def test_cross_service_group_and_inactive_ticket_are_rejected(self):
        option=self.option();other=Service.objects.create(title='Other',slug='other',summary='x',body='x')
        option.service=other
        with self.assertRaises(ValidationError):option.full_clean()
        self.data['ticketTypes'][0]['active']=False;Workspace.objects.filter(pk=1).update(data=self.data)
        option.service=self.service
        with self.assertRaises(ValueError):quote(self.service,timezone.localdate(),option)
        self.assertIsNone(attach_card_prices([self.service])[0].card_price)
    def test_admin_is_simplified_and_permissions_enforced(self):
        response=self.client.get(f'/admin/online/service/{self.service.pk}/change/')
        self.assertContains(response,'data-online-tab="tickets"');self.assertNotContains(response,'name="ticket_id"')
        response=self.client.get('/admin/online/')
        self.assertNotContains(response,'href="/admin/online/onlineprice/"');self.assertNotContains(response,'href="/admin/online/serviceoption/"')
        self.client.logout();self.assertEqual(self.client.post(f'/admin/online/serviceticketgroup/{self.group.pk}/change/',{}).status_code,302)
        user=User.objects.create_user('viewer',password='test-only',is_staff=True)
        self.client.force_login(user);self.assertEqual(self.client.get(f'/admin/online/serviceticketgroup/{self.group.pk}/change/').status_code,403)
    def test_migration_preserves_legacy_prices(self):
        self.service.ticket_id='eco';self.service.card_price_source='default';self.service.save()
        price=OnlinePrice.objects.create(service=self.service,price=600000,starts_on=timezone.localdate())
        importlib.import_module('apps.online.migrations.0011_service_ticket_management').organize(apps,None)
        price.refresh_from_db();self.assertIsNone(price.option_id)
        option=ServiceOption.objects.get(service=self.service,ticket_id='eco')
        self.assertIsNone(option.online_price);self.assertEqual(quote(self.service,timezone.localdate(),option)[0],600000)
        self.service.refresh_from_db();self.assertEqual(self.service.card_price_option_id,option.pk)
