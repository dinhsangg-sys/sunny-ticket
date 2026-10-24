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
        from django.contrib.auth.models import Permission
        self.operator.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='workspace__full_access'))
        self.agency = Agency.objects.create(legacy_id='a1',name='Agency A')
        self.agent = User.objects.create_user('agent',password='test-only',agency=self.agency)
        self.data = {'agents':[{'id':'a1','name':'Agency A'},{'id':'a2','name':'Agency B'}], 'bookings':[
            {'bookingCode':'OWN','customerType':'agent','agent':'Agency A','ticketType':'Tour','qty':1,'revenue':100,'buyPrice':60,'payments':[{'amount':20}]},
            {'bookingCode':'OTHER_SECRET','customerType':'agent','agent':'Agency B','revenue':200}], 'costPrices':[]}

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

    def secure_client(self, user=None):
        c=Client(enforce_csrf_checks=True)
        c.force_login(user or self.operator)
        c.get('/',HTTP_HOST='sn.hoianmemorieslands.com')
        return c,c.cookies['csrftoken'].value

    def test_https_origin_can_save_all_reported_modules(self):
        c,token=self.secure_client()
        data=dict(self.data,ticketTypes=[{'id':'t1','name':'Eco'}],suppliers=[{'id':'s1','name':'Supplier'}],agentPrices=[{'agent':'Agency A','ticketId':'t1','price':100}],costPrices=[{'ticketId':'t1','supplierId':'s1','price':60}],expenses=[{'title':'ship','amount':10}],zaloCampaigns=[{'id':'z1','title':'Test','recipients':[]}],cashTransactions=[])
        response=c.put('/api/state/',json.dumps({'revision':0,'data':data}),content_type='application/json',HTTP_HOST='sn.hoianmemorieslands.com',HTTP_ORIGIN='https://sn.hoianmemorieslands.com',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200)
        data['ticketTypes'][0]['hasActivity']=True
        self.assertEqual(Workspace.objects.get(pk=1).data,data)

    def test_https_origin_logout(self):
        c,token=self.secure_client()
        response=c.post('/logout/',{'csrfmiddlewaretoken':token},HTTP_HOST='sn.hoianmemorieslands.com',HTTP_ORIGIN='https://sn.hoianmemorieslands.com')
        self.assertEqual(response.status_code,302)
        self.assertNotIn('_auth_user_id',c.session)

    def test_foreign_origin_still_denied(self):
        c,token=self.secure_client()
        response=c.put('/api/state/','{}',content_type='application/json',HTTP_HOST='sn.hoianmemorieslands.com',HTTP_ORIGIN='https://untrusted.example',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,403)
        self.assertEqual(response.json()['code'],'csrf_failed')
        self.assertFalse(Workspace.objects.exists())

    def test_trusted_origin_without_token_still_denied(self):
        c,_=self.secure_client()
        response=c.put('/api/state/','{}',content_type='application/json',HTTP_HOST='sn.hoianmemorieslands.com',HTTP_ORIGIN='https://sn.hoianmemorieslands.com')
        self.assertEqual(response.status_code,403)

    def test_admin_create_group_and_user_https(self):
        from django.contrib.auth.models import Group, Permission
        admin=User.objects.create_superuser('root',password='test-admin-only')
        c,token=self.secure_client(admin)
        headers={'HTTP_HOST':'sn.hoianmemorieslands.com','HTTP_ORIGIN':'https://sn.hoianmemorieslands.com'}
        permission=Permission.objects.get(codename='view_user',content_type__app_label='accounts')
        response=c.post('/admin/auth/group/add/',{'csrfmiddlewaretoken':token,'name':'Support','permissions':[permission.pk],'_save':'Save'},**headers)
        self.assertEqual(response.status_code,302)
        group=Group.objects.get(name='Support')
        self.assertTrue(group.permissions.filter(pk=permission.pk).exists())
        response=c.post('/admin/accounts/user/add/',{'csrfmiddlewaretoken':token,'username':'new-user','password1':'Test-Password!84x','password2':'Test-Password!84x','usable_password':'true','role':'agency','agency':self.agency.pk,'_save':'Save'},**headers)
        self.assertEqual(response.status_code,302,response.content[:1500])
        new=User.objects.get(username='new-user')
        self.assertEqual(new.agency,self.agency)
        self.assertTrue(new.check_password('Test-Password!84x'))
        new.groups.add(group)
        self.assertTrue(User.objects.get(pk=new.pk).has_perm('accounts.view_user'))

    def test_admin_csrf_failure_is_readable(self):
        c,_=self.secure_client()
        response=c.post('/admin/auth/group/add/',{'name':'Denied'},HTTP_HOST='sn.hoianmemorieslands.com',HTTP_ORIGIN='https://untrusted.example')
        self.assertEqual(response.status_code,403)
        self.assertContains(response,'Yêu cầu chưa được thực hiện',status_code=403)
