from django.test import TestCase,Client,override_settings
from django.utils import timezone
from apps.legacy.models import Workspace
from apps.audit.models import AuditLog
from . import tests as legacy_tests,test_cart as cart_tests
from .models import CartOrder

@override_settings(**legacy_tests.OnlineTests._overridden_settings)
class CancellationTests(TestCase):
    setUp=legacy_tests.OnlineTests.setUp
    add=cart_tests.CartTests.add
    cart_order=cart_tests.CartTests.cart_order
    def test_admin_cancels_unpaid_cash_and_retains_history(self):
        order,_=self.cart_order();url='/cart/orders/'+str(order.pk)+'/'
        self.client.post(url,{'payment_method':'cash','cash_confirmed':'on'})
        staff=Client();staff.force_login(self.admin);process='/online/staff/cart/'+str(order.pk)+'/'
        response=staff.post(process,{'action':'cancel_order','confirmed':'on','reason':'Khách không có nhu cầu sử dụng'})
        self.assertEqual(response.status_code,302);order.refresh_from_db()
        self.assertEqual(order.status,'cancelled');self.assertEqual(order.cancelled_by,self.admin);self.assertTrue(order.cancelled_at)
        self.assertEqual(order.lines.get().status,'cancelled');self.assertEqual(Workspace.objects.get(pk=1).data.get('bookings',[]),[])
        self.assertTrue(AuditLog.objects.filter(action='online.cart.cancel:'+order.code).exists())
        queue=staff.get('/online/staff/')
        self.assertNotIn(order.pk,[row.pk for row in queue.context['carts']])
        self.assertContains(queue,'Đã hủy đơn '+order.code)
        self.assertContains(staff.get('/online/staff/?cancelled=1'),order.code)
        self.assertEqual(self.client.get(url+'status/').json()['state'],'cancelled')
        page=self.client.get(url);self.assertContains(page,'Đơn hàng đã được hủy');self.assertNotContains(page,'data-payment-methods')
        self.client.post(url,{'payment_method':'bank_transfer'});order.refresh_from_db();self.assertIsNone(order.intent_id)
    def test_staff_missing_reason_and_confirmation_cannot_cancel(self):
        order,_=self.cart_order();url='/online/staff/cart/'+str(order.pk)+'/'
        body={'action':'cancel_order','confirmed':'on','reason':'Khách yêu cầu hủy đơn'}
        self.client.force_login(self.staff);self.client.post(url,body);order.refresh_from_db();self.assertEqual(order.status,'pending')
        self.client.force_login(self.admin)
        for changes in [{'reason':''},{'confirmed':''},{'reason':'x'*1001}]:
            self.client.post(url,{**body,**changes});order.refresh_from_db();self.assertEqual(order.status,'pending')
    def test_paid_and_qr_orders_are_not_cancelled(self):
        order,_=self.cart_order();self.client.post('/cart/orders/'+str(order.pk)+'/')
        self.client.force_login(self.admin);url='/online/staff/cart/'+str(order.pk)+'/'
        body={'action':'cancel_order','confirmed':'on','reason':'Khách yêu cầu hủy đơn'}
        self.client.post(url,body);order.refresh_from_db();self.assertEqual(order.status,'pending');self.assertIsNone(order.cancelled_at)
        order.status='paid';order.paid_at=timezone.now();order.save()
        self.client.post(url,body);order.refresh_from_db();self.assertEqual(order.status,'paid');self.assertIsNone(order.cancelled_at)
