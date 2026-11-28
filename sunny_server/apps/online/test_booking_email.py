from django.test import TestCase,override_settings
from django.core import mail
from django.utils import timezone,translation
from . import tests as legacy_tests,test_cart as cart_tests
from .payments import notify_admin

@override_settings(**{**legacy_tests.OnlineTests._overridden_settings,'ONLINE_ADMIN_EMAIL':'admin@example.test','PUBLIC_SITE_URL':'https://sunnygovn.com'})
class BookingEmailTests(TestCase):
    setUp=legacy_tests.OnlineTests.setUp
    add=cart_tests.CartTests.add
    cart_order=cart_tests.CartTests.cart_order
    def test_cash_email_is_english_structured_and_not_paid(self):
        order,_=self.cart_order();order.payment_method='cash';order.cash_requested_at=timezone.now();order.delivery_note='<script>unsafe()</script>';order.save()
        with translation.override('vi'):notify_admin(order.pk)
        self.assertEqual(len(mail.outbox),1)
        message=mail.outbox[0];self.assertEqual(message.to,['admin@example.test'])
        self.assertIn('Delivery request',message.subject);self.assertIn('NOT PAID',message.body)
        html=message.alternatives[0][0]
        for text in ['Customer details','Selected experiences','Visit date','Quantity','Unit price','1,200,000 VND',order.code,order.email,order.phone,'Nov','Staff sign-in']:self.assertIn(text,html)
        self.assertIn('&lt;script&gt;',html);self.assertNotIn('<script>unsafe()',html)
        order.refresh_from_db();self.assertEqual(order.notification_state,'sent')
    def test_paid_notification_and_pending_bank_guard(self):
        order,_=self.cart_order();notify_admin(order.pk);self.assertEqual(len(mail.outbox),0)
        order.status='paid';order.save();notify_admin(order.pk)
        message=mail.outbox[0];self.assertIn('Payment received',message.subject)
        self.assertIn('Paid · Tickets awaiting fulfilment',message.alternatives[0][0])
        self.assertNotIn('NOT PAID',message.body)
