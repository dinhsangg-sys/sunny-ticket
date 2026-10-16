from io import StringIO
from tempfile import TemporaryDirectory
from django.core.management import call_command
from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.models import Session
from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.audit.models import AuditLog
from .models import Workspace, Attachment

class ResetTests(TestCase):
    def setUp(self):
        self.agency=Agency.objects.create(legacy_id='A1',name='Old')
        self.user=User.objects.create_user('owner',password='Keep-Password!1',role='admin',agency=self.agency)
        self.group=Group.objects.create(name='Keep group');self.user.groups.add(self.group)
        Workspace.objects.create(pk=1,revision=40,data={'bookings':[{'id':'old'}],'ticketMappings':[{'old':True}]})
        AuditLog.objects.create(user=self.user,action='old')
        self.client.force_login(self.user)

    def test_preview_leaves_all_data(self):
        call_command('reset_business_data',stdout=StringIO())
        self.assertEqual(Workspace.objects.get(pk=1).revision,40)
        self.assertTrue(Agency.objects.exists())
        self.assertTrue(Session.objects.exists())

    def test_execute_clears_business_preserves_login_and_invalidates_sessions(self):
        with TemporaryDirectory() as temp, self.settings(MEDIA_ROOT=temp):
            item=Attachment.objects.create(key='old',name='old.png',content_type='image/png',file=SimpleUploadedFile('old.png',b'old'))
            storage,name=item.file.storage,item.file.name
            call_command('reset_business_data',execute=True,stdout=StringIO())
            self.assertFalse(storage.exists(name))
        self.assertFalse(Attachment.objects.exists())
        self.assertFalse(Agency.objects.exists())
        self.assertFalse(AuditLog.objects.exists())
        self.assertFalse(Session.objects.exists())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Keep-Password!1'))
        self.assertIsNone(self.user.agency)
        self.assertTrue(self.user.groups.filter(pk=self.group.pk).exists())
        workspace=Workspace.objects.get(pk=1)
        self.assertEqual(workspace.revision,41)
        self.assertEqual(workspace.data['bookings'],[])
        self.assertNotIn('ticketMappings',workspace.data)

    def test_mapping_endpoint_is_removed(self):
        self.assertEqual(self.client.post('/api/pricing-preview/').status_code,404)
