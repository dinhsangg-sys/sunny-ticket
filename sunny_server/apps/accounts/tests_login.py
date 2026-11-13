from django.test import TestCase,Client,override_settings
from django.contrib.staticfiles import finders
from .models import User

@override_settings(ALLOWED_HOSTS=['testserver'])
class LoginDesignTests(TestCase):
    def setUp(self):self.user=User.objects.create_user('sunny-test',password='test-only-login-password',role='counter')
    def test_brand_accessible_fields_and_local_assets(self):
        response=self.client.get('/login/?next=/counter/')
        self.assertEqual(response.status_code,200)
        for text in ['Từ lòng người','những hành trình','csrfmiddlewaretoken','name="username"','name="password"','autocomplete="current-password"','value="/counter/"','name="next"']:self.assertContains(response,text)
        for asset in ('css/login.css','js/login.js','images/sunny-hoi-an-welcome.jpg'):self.assertIsNotNone(finders.find(asset))
    def test_valid_post_preserves_next_and_rejects_external_redirect(self):
        response=self.client.post('/login/',{'username':'sunny-test','password':'test-only-login-password','next':'/counter/'})
        self.assertRedirects(response,'/counter/',fetch_redirect_response=False)
        self.client.logout()
        response=self.client.post('/login/',{'username':'sunny-test','password':'test-only-login-password','next':'https://example.invalid/steal'})
        self.assertRedirects(response,'/',fetch_redirect_response=False)
    def test_failed_login_escapes_username_and_never_reflects_password(self):
        response=self.client.post('/login/',{'username':'"><img src=x onerror=alert(1)>','password':'do-not-reflect-this-password'})
        self.assertEqual(response.status_code,200);self.assertContains(response,'role="alert"');self.assertContains(response,'&lt;img');self.assertNotContains(response,'<img src=x');self.assertNotContains(response,'do-not-reflect-this-password')
        self.assertNotIn('_auth_user_id',self.client.session)
    def test_csrf_token_survives_custom_form(self):
        client=Client(enforce_csrf_checks=True);response=client.get('/login/')
        self.assertEqual(client.post('/login/',{'username':'sunny-test','password':'test-only-login-password'}).status_code,403)
        token=client.cookies['csrftoken'].value
        self.assertEqual(client.post('/login/',{'username':'sunny-test','password':'test-only-login-password','csrfmiddlewaretoken':token,'next':'/counter/'}).status_code,302)
