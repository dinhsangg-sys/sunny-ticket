import copy
from datetime import timedelta
from decimal import Decimal
import json
from unittest.mock import patch
from django.contrib.auth.models import Permission
from django.test import TestCase,Client
from django.utils import timezone
from apps.accounts.models import User
from . import tests_counter as fixtures
from .models import CardFeeRate,Workspace
from .card_fees import quote_fee,protect_card_receipts,fee_total

class CardFeeTests(TestCase):
    setUp=fixtures.CounterTests.setUp
    post=fixtures.CounterTests.post

    def admin(self):
        user=User.objects.create_user('fee-admin',role='admin');user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='card_fee__manage'));self.client.force_login(user);return user
    def api(self,body):return self.client.post('/api/card-fees/',json.dumps(body),content_type='application/json')
    def policy(self,**changes):return CardFeeRate.objects.create(scheme='visa',origin='domestic',rate='2.55',starts_on=timezone.localdate()-timedelta(days=1),**changes)
    def confirm(self,key,quote=None,method='card'):
        body={'version':1,'paymentRevision':0,'paymentMethod':method,'confirmed':True}
        if quote is not None:body['cardFeeQuote']=quote
        return self.client.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps(body),content_type='application/json')

    def test_management_permission_sample_and_no_business_mutation(self):
        self.assertEqual(self.api({}).status_code,403);self.assertEqual(self.client.get('/card-fees/').status_code,403)
        self.admin();before=copy.deepcopy(Workspace.objects.get(pk=1).data)
        self.assertEqual(self.api({'action':'seed','from':timezone.localdate().isoformat()}).status_code,200)
        self.assertEqual(CardFeeRate.objects.count(),10);self.assertEqual(Workspace.objects.get(pk=1).data,before)
        self.assertEqual(self.api({'action':'seed','from':timezone.localdate().isoformat()}).status_code,400)
        self.assertEqual(quote_fee('visa','foreign',1000000)['feeAmount'],35800)
        self.assertEqual(quote_fee('napas','domestic',1000000)['feeAmount'],16000)
        for scheme,domestic,foreign in [('mastercard',25000,35200),('jcb',25000,35200),('unionpay',25000,35200)]:
            self.assertEqual(quote_fee(scheme,'domestic',1000000)['feeAmount'],domestic);self.assertEqual(quote_fee(scheme,'foreign',1000000)['feeAmount'],foreign)

    def test_overlap_and_bad_rates_are_rejected_but_adjacent_periods_allowed(self):
        self.admin();day=timezone.localdate();base={'scheme':'visa','origin':'domestic','rate':'2.55','from':day.isoformat(),'to':(day+timedelta(days=3)).isoformat(),'active':True,'note':''}
        self.assertEqual(self.api(base).status_code,200);self.assertEqual(self.api(base).status_code,400)
        self.assertEqual(self.api({**base,'from':(day+timedelta(days=4)).isoformat(),'to':''}).status_code,200)
        for change in ({'rate':'101'},{'rate':'-1'},{'rate':'NaN'},{'rate':'1.1234'},{'origin':'unknown'},{'from':'bad'}):self.assertEqual(self.api({**base,**change}).status_code,400)

    def test_confirmed_card_fee_gross_paid_profit_and_historical_policy(self):
        policy=self.policy();key=self.post().json()['booking']['id'];quote=quote_fee('visa','domestic',1100000)
        result=self.confirm(key,quote);self.assertEqual(result.status_code,200,result.content);public=result.json()['booking']
        self.assertEqual(public['paid'],1100000);self.assertEqual(public['balance'],0);self.assertEqual(public['cardFee'],28050);self.assertEqual(public['netReceived'],1071950)
        row=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(row['revenue'],1100000);self.assertEqual(row['vatAmount'],45000);self.assertEqual(row['profit'],226950);snapshot=copy.deepcopy(row['payments'][0]['cardFee'])
        self.assertTrue(self.confirm(key,quote).json()['duplicate']);self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings'][0]['payments']),1)
        self.admin();value={'id':str(policy.pk),'revision':1,'scheme':'visa','origin':'domestic','rate':'3','from':policy.starts_on.isoformat(),'to':'','active':True,'note':''}
        self.assertEqual(self.api(value).status_code,400)
        self.assertEqual(self.api({**value,'rate':'2.55','to':timezone.localdate().isoformat()}).status_code,200)
        self.assertEqual(self.api({key:value for key,value in {**value,'rate':'3','from':(timezone.localdate()+timedelta(days=1)).isoformat()}.items() if key not in ('id','revision')}).status_code,200)
        self.assertEqual(quote_fee('visa','domestic',1000000,timezone.localdate()+timedelta(days=1))['feeAmount'],30000)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'][0]['cardFee'],snapshot)

    def test_missing_choices_policy_tampering_and_changed_quote_cannot_charge(self):
        key=self.post().json()['booking']['id'];self.assertEqual(self.confirm(key).status_code,400)
        with self.assertRaises(ValueError):quote_fee('visa','foreign',1100000)
        policy=self.policy();quote=quote_fee('visa','domestic',1100000)
        for change in ({'feeAmount':0},{'amount':1},{'rate':'0'},{'origin':'foreign'}):self.assertIn(self.confirm(key,{**quote,**change}).status_code,[400,409])
        policy.rate=Decimal('3');policy.revision+=1;policy.save();self.assertEqual(self.confirm(key,quote).status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'],[])

    def test_fee_uses_payment_date_not_old_booking_date_and_rounds_once(self):
        self.policy();self.assertEqual(quote_fee('visa','domestic',101)['feeAmount'],3)
        with self.assertRaises(ValueError):quote_fee('visa','domestic',1000000,timezone.localdate()-timedelta(days=2))
        key=self.post().json()['booking']['id'];obj=Workspace.objects.get(pk=1);obj.data['bookings'][0]['date']='2020-01-01';obj.save()
        response=self.client.post('/api/counter/bookings/'+key+'/card-fee-quote/',json.dumps({'scheme':'visa','origin':'domestic'}),content_type='application/json');self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['quote']['feeDate'],timezone.localdate().isoformat())

    def test_reopen_removes_current_fee_but_keeps_history_and_new_method_has_no_fee(self):
        self.policy();key=self.post().json()['booking']['id'];self.confirm(key,quote_fee('visa','domestic',1100000))
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='counter__reopen_payment'))
        response=self.client.post('/api/counter/bookings/'+key+'/reopen-payment/',json.dumps({'version':1,'paymentRevision':0,'paymentMethod':'cash','reason':'Bấm xác nhận nhầm','confirmed':True}),content_type='application/json');self.assertEqual(response.status_code,200,response.content)
        row=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(fee_total(row),0);self.assertEqual(row['profit'],255000);self.assertEqual(row['counterHistory'][-1]['paymentsBefore'][0]['cardFee']['feeAmount'],28050)
        before=Workspace.objects.get(pk=1).data;after=copy.deepcopy(before);after['bookings'][0]['counterHistory']=[]
        with self.assertRaises(ValueError):protect_card_receipts(before,after)
        response=self.client.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps({'version':1,'paymentRevision':1,'paymentMethod':'cash','confirmed':True}),content_type='application/json');self.assertEqual(response.status_code,200);self.assertEqual(response.json()['booking']['cardFee'],0)

    def test_snapshot_protected_from_general_edit_and_paid_amount_changes(self):
        self.policy();key=self.post().json()['booking']['id'];self.confirm(key,quote_fee('visa','domestic',1100000));before=Workspace.objects.get(pk=1).data
        for kind in ('fee','amount','delete','revenue','duplicate'):
            after=copy.deepcopy(before)
            if kind=='fee':after['bookings'][0]['payments'][0]['cardFee']['rate']='0'
            if kind=='amount':after['bookings'][0]['payments'][0]['amount']=1
            if kind=='delete':after['bookings']=[]
            if kind=='revenue':after['bookings'][0]['revenue']=1
            if kind=='duplicate':after['bookings'][0]['payments'].append(copy.deepcopy(after['bookings'][0]['payments'][0]))
            with self.assertRaises(ValueError):protect_card_receipts(before,after)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='counter__change'))
        result=self.client.post('/api/counter/bookings/'+key+'/',json.dumps({'version':1,'values':{'qty':3},'settled':True}),content_type='application/json');self.assertEqual(result.status_code,400)

    def test_quote_owner_csrf_and_explicit_management_permission(self):
        self.policy();key=self.post().json()['booking']['id'];other=User.objects.create_user('card-other',role='counter');other.user_permissions.add(*self.user.user_permissions.all());self.client.force_login(other)
        self.assertEqual(self.client.post('/api/counter/bookings/'+key+'/card-fee-quote/',json.dumps({'scheme':'visa','origin':'domestic'}),content_type='application/json').status_code,404)
        self.client.force_login(self.user);csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user);self.assertEqual(csrf.post('/api/counter/bookings/'+key+'/card-fee-quote/','{}',content_type='application/json').status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='card_fee__manage'));self.assertEqual(self.client.get('/api/card-fees/').status_code,403)
