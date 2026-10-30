import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from apps.accounts.models import User
from . import tests_counter as fixtures
from .models import Workspace, CounterTicketBatch
from .tests_counter_tickets import source_pdf


class CounterReopenTests(TestCase):
    setUp=fixtures.CounterTests.setUp
    post=fixtures.CounterTests.post

    def grant(self):
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='counter__reopen_payment'))

    def confirm(self,key,revision=0,method='cash'):
        return self.client.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps({'version':1,'paymentRevision':revision,'paymentMethod':method,'confirmed':True}),content_type='application/json')

    def reopen(self,key,**changes):
        return self.client.post('/api/counter/bookings/'+key+'/reopen-payment/',json.dumps({'version':1,'paymentRevision':0,'paymentMethod':'bank_transfer','reason':'Bấm nhầm xác nhận khi chưa nhận tiền','confirmed':True,**changes}),content_type='application/json')

    def paid(self):
        key=self.post().json()['booking']['id'];self.assertEqual(self.confirm(key).status_code,200);return key

    def test_permission_owner_and_csrf_are_required(self):
        key=self.paid();self.assertEqual(self.reopen(key).status_code,403)
        self.grant();other=User.objects.create_user('other-reopen',role='counter');other.user_permissions.add(*self.user.user_permissions.all());self.client.force_login(other)
        self.assertEqual(self.reopen(key).status_code,404);self.client.force_login(self.user)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post('/api/counter/bookings/'+key+'/reopen-payment/','{}',content_type='application/json').status_code,403)

    def test_audited_reopen_reconfirm_and_retry_do_not_lose_or_duplicate_money(self):
        self.grant();key=self.paid();old=copy.deepcopy(Workspace.objects.get(pk=1).data['bookings'][0]['payments'])
        result=self.reopen(key);self.assertEqual(result.status_code,200,result.content)
        row=result.json()['booking'];self.assertTrue(row['paymentPending']);self.assertEqual(row['paid'],0);self.assertEqual(row['balance'],1100000);self.assertEqual(row['paymentMethod'],'bank_transfer');self.assertEqual(row['paymentRevision'],1)
        self.assertTrue(self.reopen(key).json()['duplicate'])
        saved=Workspace.objects.get(pk=1).data['bookings'][0];entry=saved['counterHistory'][-1]
        self.assertEqual(entry['paymentsBefore'],old);self.assertEqual(entry['paymentsAfter'],[]);self.assertIn('Bấm nhầm',entry['reason']);self.assertEqual(entry['by'],self.user.username);self.assertEqual(entry['action'],'payment_reopen');self.assertEqual(saved['counterVersion'],1)
        self.assertEqual(self.confirm(key).status_code,409)
        self.assertEqual(self.confirm(key,1,'card').status_code,200)
        self.assertTrue(self.confirm(key,1,'card').json()['duplicate'])
        self.assertEqual(self.reopen(key).status_code,409)
        saved=Workspace.objects.get(pk=1).data['bookings'][0];self.assertEqual(len(saved['payments']),1);self.assertEqual(saved['payments'][0]['amount'],1100000);self.assertEqual(saved['paymentMethod'],'card')

    def test_reason_version_method_and_confirmation_validation(self):
        self.grant();key=self.paid()
        for changes in ({'reason':''},{'reason':'x'*501},{'confirmed':False},{'paymentMethod':'bad'},{'paymentRevision':True},{'paid':0}):
            self.assertEqual(self.reopen(key,**changes).status_code,400)
        self.assertEqual(self.reopen(key,version=2).status_code,409)
        self.assertEqual(self.reopen(key,paymentRevision=99).status_code,409)
        self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings'][0]['payments']),1)

    def test_provider_payments_and_old_flow_are_never_cleared(self):
        self.grant();key=self.paid();obj=Workspace.objects.get(pk=1)
        obj.data['bookings'][0]['payments'][0]['provider']='sepay';obj.save()
        self.assertEqual(self.reopen(key).status_code,400)
        self.assertFalse(self.client.get('/api/counter/bookings/'+key+'/').json()['canReopenPayment'])
        obj.data['bookings'][0]['payments'][0].pop('provider');obj.data['bookings'][0].pop('counterPaymentFlow');obj.save()
        self.assertEqual(self.reopen(key).status_code,400)

    def test_conflict_keeps_receipts_and_history(self):
        self.grant();key=self.paid();before=Workspace.objects.get(pk=1).data
        with patch('apps.legacy.counter_payment.save_workspace',side_effect=RuntimeError('conflict')):
            self.assertEqual(self.reopen(key).status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).data,before)

    def test_existing_pdf_is_blocked_until_paid_again_and_draft_version_is_preserved(self):
        self.grant();key=self.paid()
        with tempfile.TemporaryDirectory() as folder,override_settings(COUNTER_PRIVATE_ROOT=Path(folder)):
            upload=self.client.post('/api/counter/'+key+'/tickets/',{'files':SimpleUploadedFile('two.pdf',source_pdf())});self.assertEqual(upload.status_code,201,upload.content)
            batch=CounterTicketBatch.objects.get();url=f'/api/counter/ticket-batches/{batch.pk}/';payload={'confirmed':True,'rows':batch.rows}
            self.assertEqual(self.client.post(url+'generate/',json.dumps(payload),content_type='application/json').status_code,200)
            self.assertEqual(self.reopen(key).status_code,200)
            for suffix,method in [('generate/','post'),('pdf/','get'),('email/','post')]:
                self.assertEqual(getattr(self.client,method)(url+suffix).status_code,409)
            batch.refresh_from_db();self.assertEqual(batch.booking_version,1)
            self.assertEqual(self.confirm(key,1,'bank_transfer').status_code,200)
            self.assertEqual(self.client.get(url+'pdf/').status_code,200)
