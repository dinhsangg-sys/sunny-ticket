import copy
import json
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace, CounterTicketBatch
from . import tests_counter as fixtures_counter
from . import tests_counter_tickets as fixtures_ticket

def grant(user,*names):user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=names))

class CounterEditTests(TestCase):
    setUp=fixtures_counter.CounterTests.setUp
    post=fixtures_counter.CounterTests.post

    def edit(self,key,values,version=1,settled=False):return self.client.post('/api/counter/bookings/'+key+'/',json.dumps({'version':version,'values':values,'settled':settled}),content_type='application/json')

    def test_paid_creation_idempotence_and_authorized_edits(self):
        created=self.post().json()['booking'];key=created['id'];created=self.client.post('/api/counter/bookings/'+key+'/confirm-payment/',json.dumps({'version':1,'paymentMethod':'cash','confirmed':True}),content_type='application/json').json()['booking'];self.assertEqual(created['paid'],created['revenue']);self.assertEqual(created['balance'],0)
        self.post();self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings'][0]['payments']),1)
        self.assertEqual(self.edit(key,{'note':'new'}).status_code,403)
        grant(self.user,'counter__change')
        self.assertEqual(self.edit(key,{'note':'new'}).status_code,200)
        self.assertEqual(self.edit(key,{'note':'stale'}).status_code,409)
        self.assertEqual(self.edit(key,{'date':'2000-01-01'},2).status_code,400)
        self.assertEqual(self.edit(key,{'sellPrice':600000},2,True).status_code,400)
        grant(self.user,'counter__settle_adjustment')
        self.assertEqual(self.edit(key,{'sellPrice':600000},2).status_code,400)
        self.assertEqual(self.edit(key,{'sellPrice':600000},2,True).status_code,200)
        self.assertEqual(self.edit(key,{'sellPrice':500000},3,True).status_code,200)
        row=Workspace.objects.get(pk=1).data['bookings'][0]
        self.assertEqual(sum(p['amount'] for p in row['payments']),1000000)
        self.assertEqual(row['counterHistory'][-1]['paymentAdjustment'],-200000)
        self.assertEqual(sum(p['amount'] for p in row['counterHistory'][-1]['paymentsBefore']),1200000)
        detail=self.client.get('/api/counter/bookings/'+key+'/');self.assertNotIn('buyPrice',detail.content.decode())
        other=User.objects.create_user('other',role='counter');grant(other,'counter__view','counter__change');self.client.force_login(other)
        self.assertEqual(self.client.get('/api/counter/bookings/'+key+'/').status_code,404)
        self.assertEqual(self.edit(key,{'note':'attack'},4).status_code,404)

class CounterRevisionTests(TestCase):
    setUp=fixtures_ticket.CounterTicketTests.setUp
    tearDown=fixtures_ticket.CounterTicketTests.tearDown
    upload=fixtures_ticket.CounterTicketTests.upload
    generate=fixtures_ticket.CounterTicketTests.generate

    def test_report_reads_actual_pdf_and_flags_modified_information(self):
        self.upload();batch=CounterTicketBatch.objects.get();self.assertEqual(self.generate(batch).status_code,200)
        self.assertEqual(self.client.get('/api/counter/report/').status_code,403)
        grant(self.user,'counter__report')
        result=self.client.get('/api/counter/report/'+str(batch.pk)+'/');self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['status'],'match',result.json())
        self.assertTrue(result.json()['verifiedPdf']);self.assertTrue(all(r['qrMatch'] for r in result.json()['details']))
        file=self.client.get('/api/counter/report/'+str(batch.pk)+'/file/');self.assertEqual(file.status_code,200);file.close()
        grant(self.user,'counter__replace_tickets')
        cloned=self.client.post('/api/counter/ticket-batches/'+str(batch.pk)+'/replace/',{},content_type='application/json');self.assertEqual(cloned.status_code,201)
        next_batch=CounterTicketBatch.objects.get(pk=cloned.json()['id']);changed=copy.deepcopy(next_batch.rows);changed[0]['package']='CHANGED PACKAGE'
        self.assertEqual(self.generate(next_batch,changed).status_code,200)
        result=self.client.get('/api/counter/report/'+str(next_batch.pk)+'/').json();self.assertEqual(result['status'],'different',result)
        batch.refresh_from_db();self.assertIsNotNone(batch.superseded_at)
        self.assertEqual(self.client.post('/api/counter/ticket-batches/'+str(batch.pk)+'/email/',{},content_type='application/json').status_code,409)
        self.assertEqual(CounterTicketBatch.objects.count(),2)

    def test_replacement_permission_and_booking_version_block(self):
        self.upload();batch=CounterTicketBatch.objects.get();self.generate(batch)
        self.assertEqual(self.client.post('/api/counter/ticket-batches/'+str(batch.pk)+'/replace/',{},content_type='application/json').status_code,403)
        data=Workspace.objects.get(pk=1).data;data['bookings'][0]['counterVersion']=2;Workspace.objects.filter(pk=1).update(data=data)
        self.assertEqual(self.generate(batch).status_code,400)
        grant(self.user,'counter__replace_tickets')
        clone=self.client.post('/api/counter/ticket-batches/'+str(batch.pk)+'/replace/',{},content_type='application/json').json()
        new=CounterTicketBatch.objects.get(pk=clone['id']);self.assertEqual(new.booking_version,2);self.assertEqual(self.generate(new).status_code,200)

    def test_report_all_permission_does_not_grant_edit_or_other_staff_private_api(self):
        self.upload();batch=CounterTicketBatch.objects.get();self.generate(batch)
        other=User.objects.create_user('report-manager',role='counter');grant(other,'counter__view','counter__report');self.client.force_login(other)
        self.assertEqual(self.client.get('/api/counter/report/').json()['rows'],[])
        self.assertEqual(self.client.get('/api/counter/report/'+str(batch.pk)+'/').status_code,404)
        grant(other,'counter__report_all')
        self.assertEqual(len(self.client.get('/api/counter/report/').json()['rows']),1)
        self.assertEqual(self.client.get('/api/counter/report/'+str(batch.pk)+'/').status_code,200)
        self.assertEqual(self.client.get('/api/counter/ticket-batches/'+str(batch.pk)+'/pdf/').status_code,404)
        self.assertEqual(self.client.get('/api/counter/report/?status=missing').json()['rows'],[])
