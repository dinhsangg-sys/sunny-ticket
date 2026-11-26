import json
from unittest.mock import patch
from django.test import TestCase,Client,override_settings
from django.core.cache import cache
from apps.accounts.models import User
from .models import Service,ServiceFAQ

@override_settings(ALLOWED_HOSTS=['testserver','sunnygovn.com'],SUNNY_CHAT_ENABLED=True)
class ChatTests(TestCase):
    def setUp(self):
        cache.clear();self.client.cookies['sunny_lang']='vi'
        self.service=Service.objects.create(title='Ký Ức Hội An',title_en='Hoi An Memories',slug='chat-service',ticket_id='',summary='Nội dung công khai',body='Giới thiệu dịch vụ',published=True)
        self.faq=ServiceFAQ.objects.create(service=self.service,question='Giờ mở cửa là mấy giờ?',question_en='What are the opening hours?',keywords='giờ mở cửa, opening hours, mo cua luc',answer='Thời gian minh họa đã duyệt: 16:00–22:00.',answer_en='Approved fixture hours: 16:00–22:00.',active=True)
    def ask(self,message,service=None,client=None,lang='vi'):
        return (client or self.client).post('/api/public/chat/ask/?lang='+lang,json.dumps({'service':service or self.service.pk,'message':message}),content_type='application/json')
    def test_only_published_services_and_approved_faq_in_selected_service(self):
        hidden=Service.objects.create(title='Private draft',slug='private-chat',summary='x',body='secret')
        ServiceFAQ.objects.create(service=self.service,question='Chỗ gửi đồ?',keywords='gửi đồ',answer='Private draft answer',active=False)
        other=Service.objects.create(title='Other',slug='other-chat',summary='x',body='x',published=True)
        ServiceFAQ.objects.create(service=other,question='Đỗ xe ở đâu?',keywords='đỗ xe',answer='OTHER SERVICE ONLY',active=True)
        data=self.client.get('/api/public/chat/services/?lang=vi').json();self.assertNotIn(hidden.pk,[s['id'] for s in data['services']]);self.assertEqual(data['mode'],'local_faq');self.assertTrue(data['csrf_token'])
        self.assertEqual(self.ask('giờ mở cửa',service=hidden.pk).status_code,404)
        self.assertTrue(self.ask('gửi đồ').json()['handoff']);self.assertNotIn('Private draft answer',str(self.ask('gửi đồ').json()))
        self.assertTrue(self.ask('đỗ xe').json()['handoff']);self.assertNotIn('OTHER SERVICE ONLY',str(self.ask('đỗ xe').json()))
    def test_keywords_accents_english_and_safe_plain_response_no_network(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('No external API permitted')) as network:
            for question in ['Giờ mở cửa là mấy giờ?','cho hoi gio mo cua cua dich vu','MỞ CỬA LÚC NÀO?']:
                data=self.ask(question).json();self.assertFalse(data['handoff']);self.assertEqual(data['answer'],self.faq.answer)
            data=self.ask('opening hours?',lang='en').json();self.assertEqual(data['answer'],self.faq.answer_en);network.assert_not_called()
        self.faq.answer='<script>alert(1)</script>';self.faq.save();self.assertEqual(self.ask('giờ mở cửa').json()['answer'],self.faq.answer)
    def test_unknown_ambiguous_and_missing_english_handoff(self):
        data=self.ask('Có hướng dẫn viên riêng không?').json();self.assertTrue(data['handoff']);self.assertEqual([c['label'] for c in data['contacts']],['WhatsApp','Zalo'])
        ServiceFAQ.objects.create(service=self.service,question='Giờ mở cửa ngày đặc biệt?',keywords='giờ mở cửa',answer='Special day answer',active=True)
        self.assertTrue(self.ask('giờ mở cửa').json()['handoff']);self.assertGreaterEqual(len(self.ask('giờ mở cửa').json()['suggestions']),2)
        self.assertFalse(self.ask(self.faq.question).json()['handoff'])
        self.faq.answer_en='';self.faq.save();self.assertTrue(self.ask('opening hours',lang='en').json()['handoff'])
    def test_prices_link_live_picker_personal_requests_handoff_and_no_booking_actions(self):
        data=self.ask('giá vé bao nhiêu?').json();self.assertEqual(data['service_url'],'/services/chat-service/');self.assertNotIn('300.000',data['answer'])
        for question in ['Tôi muốn gặp nhân viên','Tôi chưa nhận vé','refund for booking','SC-123456 order','email guest@example.test']:
            self.assertTrue(self.ask(question).json()['handoff'])
        self.assertNotContains(self.client.get('/api/public/chat/services/'),'booking_id')
    def test_validation_rate_limit_disabled_and_csrf(self):
        url='/api/public/chat/ask/'
        for payload in [{},{'service':True,'message':'hello'},{'service':self.service.pk,'message':'x'*601},{'service':self.service.pk,'message':'hello','booking_id':'private'}]:self.assertEqual(self.client.post(url,json.dumps(payload),content_type='application/json').status_code,400)
        cache.clear()
        for i in range(20):self.assertEqual(self.ask('giờ mở cửa').status_code,200)
        self.assertEqual(self.ask('giờ mở cửa').status_code,429)
        cache.clear();guest=Client(enforce_csrf_checks=True)
        self.assertEqual(self.ask('giờ mở cửa',client=guest).status_code,403)
        init=guest.get('/api/public/chat/services/?lang=vi').json();response=guest.post(url+'?lang=vi',json.dumps({'service':self.service.pk,'message':'giờ mở cửa'}),content_type='application/json',HTTP_X_CSRFTOKEN=init['csrf_token']);self.assertEqual(response.status_code,200)
        with self.settings(SUNNY_CHAT_ENABLED=False):
            self.assertEqual(self.client.get('/api/public/chat/services/').status_code,404)
            self.assertNotContains(self.client.get('/discover/'),'class="chat-toggle"')
    def test_widget_public_pages_and_admin_faq_fields(self):
        self.assertContains(self.client.get('/discover/'),'id="chat-service"')
        with self.settings(SOUVENIRS_ENABLED=True):self.assertContains(self.client.get('/souvenirs/catalog/'),'id="sunny-chat"')
        admin=User.objects.create_superuser('chat-admin',password='test-only',role='admin');self.client.force_login(admin)
        self.assertContains(self.client.get('/admin/online/servicefaq/add/'),'name="keywords"')
