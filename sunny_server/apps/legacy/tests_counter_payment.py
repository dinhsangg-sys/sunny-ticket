import copy
import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User
from .models import Workspace, CounterTicketBatch, CounterIssuedQR
from . import tests_counter as fixtures
from .tests_counter_tickets import source_pdf

class CounterPaymentTests(TestCase):
    setUp=fixtures.CounterTests.setUp
    post=fixtures.CounterTests.post

    def confirm(self,key,method='cash',version=1,**extra):
        return self.client.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps({'version':version,'paymentMethod':method,'confirmed':True,**extra}),content_type='application/json')

    def test_default_and_three_methods_require_explicit_acknowledgment_and_are_idempotent(self):
        for method in ('cash','card','bank_transfer'):
            body={**self.body,'requestId':str(uuid.uuid4())}
            if method!='cash':body['paymentMethod']=method
            created=self.post(body).json()['booking'];key=created['id']
            self.assertTrue(created['paymentPending']);self.assertEqual(created['paid'],0);self.assertEqual(created['balance'],1100000);self.assertEqual(created['paymentMethod'],method)
            result=self.confirm(key,method);self.assertEqual(result.status_code,200,result.content);self.assertFalse(result.json()['booking']['paymentPending']);self.assertEqual(result.json()['booking']['paymentStatus'],'completed')
            self.assertTrue(self.confirm(key,method).json()['duplicate'])
            row=next(b for b in Workspace.objects.get(pk=1).data['bookings'] if b['id']==key)
            self.assertEqual(len(row['payments']),1);self.assertEqual(row['payments'][0]['amount'],1100000);self.assertEqual(row['payments'][0]['method'],method)
            self.assertEqual(row['counterPaymentConfirmedBy'],self.user.username);self.assertTrue(row['counterPaymentConfirmedAt']);self.assertEqual(row['counterVersion'],1)
            self.assertNotIn('buyPrice',result.content.decode())

    def test_pending_edit_does_not_collect_money_and_stale_confirmation_is_blocked(self):
        key=self.post().json()['booking']['id']
        self.user.user_permissions.add(Permission.objects.get(codename='counter__change',content_type__app_label='legacy'))
        edit=self.client.post('/api/counter/bookings/'+key+'/',json.dumps({'version':1,'values':{'qty':3,'paymentMethod':'card'},'settled':True}),content_type='application/json')
        self.assertEqual(edit.status_code,200,edit.content);self.assertEqual(edit.json()['booking']['paid'],0);self.assertTrue(edit.json()['booking']['paymentPending'])
        self.assertEqual(self.confirm(key,'card',1).status_code,409)
        self.assertEqual(self.confirm(key,'card',2).json()['booking']['paid'],1650000)
        self.assertEqual(self.confirm(key,'bank_transfer',2).status_code,400)

    def test_confirmation_validation_conflict_and_permission_boundaries(self):
        for value in ('bad',[],None):self.assertEqual(self.post({**self.body,'paymentMethod':value}).status_code,400)
        key=self.post().json()['booking']['id']
        self.assertEqual(self.confirm(key,confirmed=False).status_code,400)
        self.assertEqual(self.confirm(key,amount=1).status_code,400)
        self.assertEqual(self.confirm(key,'invalid').status_code,400)
        with patch('apps.legacy.counter_payment.save_workspace',side_effect=RuntimeError('conflict')):self.assertEqual(self.confirm(key).status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['payments'],[])
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps({'version':1,'confirmed':True}),content_type='application/json').status_code,403)
        other=User.objects.create_user('other-payment',role='counter');other.user_permissions.add(*self.user.user_permissions.all());self.client.force_login(other)
        self.assertEqual(self.confirm(key).status_code,404)
        self.client.force_login(self.user);self.user.user_permissions.remove(Permission.objects.get(codename='counter__create',content_type__app_label='legacy'))
        self.assertEqual(self.confirm(key).status_code,403)

    def test_zero_price_requires_confirmation_and_old_booking_is_not_reclassified(self):
        key=self.post({**self.body,'sellPrice':0}).json()['booking']['id']
        self.assertTrue(self.client.get('/api/counter/').json()['bookings'][0]['paymentPending'])
        self.assertEqual(self.confirm(key).json()['booking']['paymentStatus'],'completed')
        row=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(row['payments'],[])
        obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);old={**row,'id':'legacy','bookingCode':'OLD','payments':[{'date':'2026-01-01','amount':0}],'status':'completed'}
        for field in ('counterPaymentFlow','counterPaymentConfirmedAt','counterPaymentConfirmedBy','paymentMethod'):old.pop(field,None)
        data['bookings'].append(old);obj.data=data;obj.save()
        self.assertEqual(self.confirm('legacy').status_code,400);self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][-1],old)

    def test_pending_import_allowed_but_export_and_email_blocked_until_confirmation(self):
        key=self.post().json()['booking']['id']
        with tempfile.TemporaryDirectory() as folder,override_settings(COUNTER_PRIVATE_ROOT=Path(folder)):
            upload=self.client.post('/api/counter/'+key+'/tickets/',{'files':SimpleUploadedFile('two.pdf',source_pdf())});self.assertEqual(upload.status_code,201,upload.content)
            batch=CounterTicketBatch.objects.get();payload={'confirmed':True,'rows':batch.rows}
            url=f'/api/counter/ticket-batches/{batch.pk}/'
            self.assertEqual(self.client.post(url+'generate/',json.dumps(payload),content_type='application/json').status_code,409)
            self.assertEqual(self.client.post(url+'email/',{},content_type='application/json').status_code,409)
            self.assertEqual(CounterIssuedQR.objects.count(),0)
            self.assertEqual(self.confirm(key).status_code,200)
            result=self.client.post(url+'generate/',json.dumps(payload),content_type='application/json');self.assertEqual(result.status_code,200,result.content)
            self.assertEqual(CounterIssuedQR.objects.count(),2)
