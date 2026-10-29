from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User

class ReportNavigationTests(TestCase):
    def test_superuser_has_report_links_in_main_and_admin(self):
        user=User.objects.create_superuser('mmap-test',password='test-password',role='admin');self.client.force_login(user)
        self.assertContains(self.client.get('/'),'href="/counter/report/"')
        self.assertContains(self.client.get('/admin/'),'Báo cáo đối chiếu vé')
        self.assertEqual(self.client.get('/counter/report/').status_code,200)

    def test_staff_without_report_permissions_gets_link_and_instructions_not_data(self):
        user=User.objects.create_user('limited-admin',role='admin',is_staff=True);self.client.force_login(user)
        self.assertContains(self.client.get('/'),'href="/counter/report/"')
        self.assertContains(self.client.get('/admin/'),'Báo cáo đối chiếu vé')
        response=self.client.get('/counter/report/');self.assertEqual(response.status_code,403)
        self.assertContains(response,'counter__report_all',status_code=403);self.assertContains(response,'limited-admin',status_code=403)
        self.assertEqual(self.client.get('/api/counter/report/').status_code,403)
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['counter__view','counter__report','counter__report_all']))
        self.assertEqual(self.client.get('/counter/report/').status_code,200)
