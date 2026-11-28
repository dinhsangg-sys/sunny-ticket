from datetime import timedelta
from django.test import TestCase,Client,override_settings
from django.utils import timezone
from apps.legacy.models import Workspace
from .models import CartOrder
from . import tests as legacy_tests
from . import test_cart as cart_tests

@override_settings(**{**legacy_tests.OnlineTests._overridden_settings,'ONLINE_ADMIN_EMAIL':'admin@example.test'})
class MethodTests(TestCase):
    setUp=legacy_tests.OnlineTests.setUp
    add=cart_tests.CartTests.add
    cart_order=cart_tests.CartTests.cart_order
    def cash(self,order):
        return self.client.post('/cart/orders/'+str(order.pk)+'/',{'payment_method':'cash','cash_confirmed':'on','delivery_note':'Khách sạn tại Đà Nẵng'})
    def test_cash_request_is_private_idempotent_and_not_revenue(self):
        order,_=self.cart_order()
        with self.captureOnCommitCallbacks(execute=True):self.assertEqual(self.cash(order).status_code,302)
        order.refresh_from_db();self.assertEqual(order.status,'pending');self.assertEqual(order.payment_method,'cash');self.assertIsNotNone(order.cash_requested_at);self.assertIsNone(order.intent_id)
        self.assertEqual(Workspace.objects.get(pk=1).data.get('bookings',[]),[])
        self.assertEqual(self.cash(order).status_code,302)
        self.assertEqual(self.client.get('/cart/orders/'+str(order.pk)+'/status/').json()['state'],'cash_pending')
        self.assertEqual(Client().get('/cart/orders/'+str(order.pk)+'/').status_code,404)
        self.client.force_login(self.staff);self.assertContains(self.client.get('/online/staff/'),order.code)
    def test_cards_and_cash_after_qr_are_blocked(self):
        order,_=self.cart_order();url='/cart/orders/'+str(order.pk)+'/'
        for method in ('visa','mastercard','unknown'):
            self.assertEqual(self.client.post(url,{'payment_method':method}).status_code,200)
            order.refresh_from_db();self.assertIsNone(order.intent_id)
        self.assertEqual(self.client.post(url).status_code,200);order.refresh_from_db();self.assertIsNotNone(order.intent_id)
        self.cash(order);order.refresh_from_db();self.assertEqual(order.payment_method,'bank_transfer');self.assertIsNone(order.cash_requested_at)
    def test_cash_collect_requires_permission_exact_amount_and_confirmed_delivery(self):
        order,_=self.cart_order();self.cash(order);url='/online/staff/cart/'+str(order.pk)+'/'
        body={'action':'collect_cash','confirmed':'on','cash_amount':str(order.total),'note':'Đã giao vé đúng khách và thu đủ tiền'}
        self.client.force_login(self.staff);self.client.post(url,body);order.refresh_from_db();self.assertEqual(order.status,'pending')
        self.client.force_login(self.admin)
        for changes in [{'cash_amount':'1'},{'confirmed':''},{'note':'x'}]:
            self.client.post(url,{**body,**changes});order.refresh_from_db();self.assertEqual(order.status,'pending')
        self.assertEqual(self.client.post(url,body).status_code,302);order.refresh_from_db();self.assertEqual(order.status,'paid')
        rows=Workspace.objects.get(pk=1).data['bookings'];self.assertEqual(len(rows),1);self.assertEqual(rows[0]['agent'],'Digital');self.assertEqual(rows[0]['payments'][0]['method'],'cash');self.assertEqual(rows[0]['payments'][0]['amount'],order.total)
        self.client.post(url,body);self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings']),1)
    def test_expiry_cash_without_confirmation_and_qr_after_cash(self):
        order,_=self.cart_order();url='/cart/orders/'+str(order.pk)+'/'
        self.client.post(url,{'payment_method':'cash'});order.refresh_from_db();self.assertIsNone(order.cash_requested_at)
        CartOrder.objects.filter(pk=order.pk).update(created_at=timezone.now()-timedelta(minutes=31));self.cash(order);order.refresh_from_db();self.assertIsNone(order.cash_requested_at)
        CartOrder.objects.filter(pk=order.pk).update(created_at=timezone.now());self.cash(order)
        self.client.post(url,{'payment_method':'bank_transfer'});order.refresh_from_db();self.assertIsNone(order.intent_id)
    def test_https_csrf_same_origin_succeeds_and_cross_site_fails(self):
        order,_=self.cart_order();url='/cart/orders/'+str(order.pk)+'/'
        secure=Client(enforce_csrf_checks=True);secure.cookies=self.client.cookies.copy()
        response=secure.get(url,secure=True);self.assertEqual(response['Referrer-Policy'],'same-origin')
        token=secure.cookies['csrftoken'].value
        response=secure.post(url,{'csrfmiddlewaretoken':token,'payment_method':'mastercard'},secure=True,HTTP_REFERER='https://testserver'+url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(secure.post(url,{'csrfmiddlewaretoken':token},secure=True,HTTP_ORIGIN='https://untrusted.example').status_code,403)
