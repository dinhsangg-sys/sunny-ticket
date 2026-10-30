import copy
import json
from django.test import TestCase, Client, override_settings
from django.core import mail
from apps.accounts.models import User
from .models import Workspace, CounterTicketBatch
from .counter_email_template import checked_message
from . import tests_counter_tickets as fixtures

class CounterEmailTemplateTests(TestCase):
    setUp=fixtures.CounterTicketTests.setUp
    tearDown=fixtures.CounterTicketTests.tearDown
    upload=fixtures.CounterTicketTests.upload
    generate=fixtures.CounterTicketTests.generate

    def set_template(self,subject='Vé {{ma_booking}}',body='Kính gửi {{email_khach}},\nLoại vé: {{loai_ve}}\nSL {{so_luong}} · {{tong_tien}}\n{{phuong_thuc_thanh_toan}}'):
        obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);data.setdefault('settings',{})['counterEmailTemplate']={'subject':subject,'body':body};data['bookings'][0].update(ticketType='Eco',revenue=1000000,date='2026-10-30',agent='nv1',paymentMethod='bank_transfer');obj.data=data;obj.save()

    def test_shared_template_permissions_validation_revision_and_no_send_on_save(self):
        url='/api/counter/email-template/';self.assertFalse(self.client.get(url).json()['canManage'])
        body={'revision':0,'subject':'Vé {{ma_booking}}','body':'Xin chào, PDF được đính kèm.'}
        self.assertEqual(self.client.post(url,json.dumps(body),content_type='application/json').status_code,403)
        admin=User.objects.create_superuser('email-admin',password='test-password',role='admin');self.client.force_login(admin)
        self.assertContains(self.client.get('/counter/email-template/'),'Mẫu email gửi vé')
        self.assertEqual(self.client.post(url,json.dumps({**body,'subject':'Hi\nBcc: bad@example.com'}),content_type='application/json').status_code,400)
        self.assertEqual(self.client.post(url,json.dumps({**body,'body':'{{gia_von}}'}),content_type='application/json').status_code,400)
        response=self.client.post(url,json.dumps(body),content_type='application/json');self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'],self.data['bookings'])
        self.assertEqual(self.client.post(url,json.dumps(body),content_type='application/json').status_code,409)
        self.assertFalse(getattr(mail,'outbox',[]))
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(admin)
        self.assertEqual(csrf.post(url,json.dumps({**body,'revision':1}),content_type='application/json').status_code,403)

    def test_rendered_template_uses_booking_and_recipient_with_real_pdf_attachment(self):
        self.set_template();self.upload();self.generate();batch=CounterTicketBatch.objects.get()
        draft=self.client.get(f'/api/counter/ticket-batches/{batch.pk}/email-draft/?email=new@example.com').json()
        self.assertEqual(draft['subject'],'Vé ST-TEST');self.assertIn('new@example.com',draft['body']);self.assertIn('1.000.000 đ',draft['body']);self.assertIn('Chuyển khoản',draft['body'])
        with override_settings(COUNTER_EMAIL_ENABLED=True):
            response=self.client.post(f'/api/counter/ticket-batches/{batch.pk}/email/',json.dumps({'email':'new@example.com','confirmed':True}),content_type='application/json')
        self.assertEqual(response.status_code,200,response.content);self.assertEqual(len(mail.outbox),1)
        self.assertEqual(mail.outbox[0].subject,draft['subject']);self.assertEqual(mail.outbox[0].body,draft['body']);self.assertEqual(mail.outbox[0].to,['new@example.com'])
        attachment=mail.outbox[0].attachments[0];self.assertEqual(attachment[2],'application/pdf');self.assertTrue(attachment[1].startswith(b'%PDF-'))
        batch.refresh_from_db();self.assertEqual(batch.email_subject,draft['subject']);self.assertEqual(batch.email_body,draft['body'])

    def test_custom_message_validation_and_changed_content_not_silently_sent_twice(self):
        self.upload();self.generate();batch=CounterTicketBatch.objects.get();url=f'/api/counter/ticket-batches/{batch.pk}/email/'
        body={'email':'guest@example.com','confirmed':True,'subject':'Vé của Quý khách','body':'Kính gửi Quý khách,\n\nVé nằm trong file PDF đính kèm.\nCảm ơn!'}
        with override_settings(COUNTER_EMAIL_ENABLED=True):
            self.assertEqual(self.client.post(url,json.dumps({**body,'subject':'X\nBcc: bad@example.com'}),content_type='application/json').status_code,400)
            self.assertEqual(self.client.post(url,json.dumps({**body,'body':''}),content_type='application/json').status_code,400)
            self.assertEqual(self.client.post(url,json.dumps(body),content_type='application/json').status_code,200)
            self.assertEqual(self.client.post(url,json.dumps(body),content_type='application/json').status_code,200)
            self.assertEqual(self.client.post(url,json.dumps({**body,'body':'Nội dung mới'}),content_type='application/json').status_code,409)
        self.assertEqual(len(mail.outbox),1);self.assertEqual(mail.outbox[0].body,body['body'])

    def test_bad_shared_template_does_not_block_viewing_or_manual_composition(self):
        self.set_template(body='{{unsupported}}');self.upload();self.generate();batch=CounterTicketBatch.objects.get()
        response=self.client.get('/api/counter/booking/tickets/');self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['batches'][0]['emailDraftError'])
        with override_settings(COUNTER_EMAIL_ENABLED=True):
            result=self.client.post(f'/api/counter/ticket-batches/{batch.pk}/email/',json.dumps({'email':'guest@example.com','confirmed':True,'subject':'Vé','body':'Xin kiểm tra PDF đính kèm.'}),content_type='application/json')
        self.assertEqual(result.status_code,200,result.content)
        with self.assertRaises(ValueError):checked_message('Vé {{unknown}}','Nội dung',template=True)
