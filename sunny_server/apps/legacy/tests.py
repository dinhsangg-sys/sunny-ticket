import json
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.audit.models import AuditLog
from .models import Workspace

class ServerTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user('operator',password='test-only',role='operator')
        self.agency = Agency.objects.create(legacy_id='a1',name='Agency A')
        self.agent = User.objects.create_user('agent',password='test-only',agency=self.agency)
        self.data = {'agents':[{'id':'a1','name':'Agency A'},{'id':'a2','name':'Agency B'}], 'bookings':[
            {'bookingCode':'OWN','customerType':'agent','agent':'Agency A','ticketType':'Tour','qty':1,'revenue':100,'buyPrice':60,'payments':[{'amount':20}]},
            {'bookingCode':'OTHER_SECRET','customerType':'agent','agent':'Agency B','revenue':200}], 'costPrices':[{'secret':12345}]}

    def save(self,revision=0,data=None):
        return self.client.put('/api/state/',json.dumps({'revision':revision,'data':self.data if data is None else data}),content_type='application/json')

    def test_login_required(self):
        self.assertEqual(self.client.get('/api/state/').status_code,302)

    def test_shared_state_and_conflict(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.save().status_code,200)
        self.assertEqual(self.save().status_code,409)
        self.assertEqual(Workspace.objects.get(pk=1).revision,1)
        self.assertEqual(AuditLog.objects.count(),1)
        self.assertEqual(self.client.get('/api/state/').json()['data'],self.data)

    def test_agency_scope_and_write_denied(self):
        Workspace.objects.create(pk=1,data=self.data)
        self.client.force_login(self.agent)
        response=self.client.get('/')
        self.assertContains(response,'OWN')
        self.assertNotContains(response,'OTHER_SECRET')
        self.assertNotContains(response,'buyPrice')
        self.assertEqual(self.client.get('/api/state/').status_code,403)
        self.assertEqual(self.save().status_code,403)
        self.assertEqual(self.client.get('/api/media/secret/').status_code,403)

    def test_ambiguous_agency_name_denied(self):
        self.data['agents'][1]['name']='Agency A'
        Workspace.objects.create(pk=1,data=self.data)
        self.client.force_login(self.agent)
        self.assertNotContains(self.client.get('/'),'OWN')

    def test_csrf_required(self):
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.operator)
        self.assertEqual(c.put('/api/state/','{}',content_type='application/json').status_code,403)

    def test_invalid_data_does_not_replace(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.save(data={'agents':['bad']}).status_code,400)
        self.assertEqual(Workspace.objects.get(pk=1).revision,0)

    def test_media_access(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp, self.settings(MEDIA_ROOT=tmp):
            self.client.force_login(self.operator)
            f=SimpleUploadedFile('test.png',b'test-image',content_type='image/png')
            self.assertEqual(self.client.post('/api/media/test/',{'file':f}).status_code,200)
            response=self.client.get('/api/media/test/')
            self.assertEqual(response.status_code,200)
            self.assertEqual(b''.join(response.streaming_content),b'test-image')
            response.close()
            self.assertEqual(self.client.delete('/api/media/test/').status_code,200)

    def test_internal_page(self):
        self.client.force_login(self.operator)
        response=self.client.get('/')
        self.assertContains(response,'/static/js/legacy.js')
        self.assertContains(response,'csrfmiddlewaretoken')
