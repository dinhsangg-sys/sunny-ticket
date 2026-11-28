import copy,json,tempfile,uuid
from io import BytesIO
from unittest.mock import patch
from django.test import TestCase,Client,override_settings
from django.core import mail
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from apps.accounts.models import User
from apps.legacy.models import Workspace,SePayIntent,SePayTransaction
from .models import Service,ServiceOption,OnlinePrice,OnlineOrder,CartOrder,OrderTicket
from . import tests as legacy_tests
from .views import quote

@override_settings(**{**legacy_tests.OnlineTests._overridden_settings,'ONLINE_ADMIN_EMAIL':'admin@example.test'})
class CartTests(TestCase):
    setUp=legacy_tests.OnlineTests.setUp
    hook=legacy_tests.OnlineTests.hook
    def add(self,service=None,**body):
        return self.client.post('/services/'+(service or self.service).slug+'/add/',{'visit_date':self.day.isoformat(),'qty_default':'2',**body})
    def cart_order(self):
        self.add()
        response=self.client.get('/cart/checkout/')
        form=response.context['form']
        body={'request_id':str(form.initial['request_id']),'quote_token':form.initial['quote_token'],'customer_name':'Cart guest','email':'guest@example.test','phone_country':'+84','phone':'+84932548145','agreed':'on'}
        response=self.client.post('/cart/checkout/',body)
        self.assertEqual(response.status_code,302,response.content)
        order=CartOrder.objects.get(request_id=body['request_id'])
        return order,body
    def paid(self):
        order,body=self.cart_order();self.client.post('/cart/orders/'+str(order.pk)+'/');order.refresh_from_db()
        with self.captureOnCommitCallbacks(execute=True):self.assertEqual(self.hook(order.intent).json()['state'],'applied')
        order.refresh_from_db();return order
    def test_variants_prices_separate_from_default_and_article_layout(self):
        option=ServiceOption.objects.create(service=self.service,title='ECO · Trẻ em',title_en='ECO · Child',ticket_id='eco')
        OnlinePrice.objects.create(service=self.service,option=option,price=300000,starts_on=timezone.localdate())
        self.assertEqual(quote(self.service,self.day)[0],600000);self.assertEqual(quote(self.service,self.day,option)[0],300000)
        page=self.client.get('/services/hoi-an/');self.assertContains(page,'service-layout');self.assertContains(page,'ECO · Trẻ em');self.assertContains(page,'&lt;script&gt;')
        data=self.client.get('/services/hoi-an/prices/',{'date':str(self.day)}).json()
        self.assertEqual([row['price'] for row in data['options']],[600000,300000]);self.assertNotIn('supplier',str(data))
        response=self.add(qty_default='1',**{'qty_'+str(option.pk):'2'})
        self.assertEqual(response.status_code,302)
        page=self.client.get('/cart/');self.assertEqual(page.context['total'],1200000)
        other=Service.objects.create(title='Other',slug='other',ticket_id='eco',summary='x',body='x',published=True)
        price=OnlinePrice(service=other,option=option,price=1,starts_on=self.day)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):price.full_clean()
    def test_cart_selections_quantity_remove_and_invalid_dates(self):
        for values in [{'qty_default':'-1'},{'qty_default':'21'},{'visit_date':'2000-01-01'},{'qty_default':'0'}]:self.assertEqual(self.add(**values).status_code,200)
        self.assertEqual(self.client.session.get('sunny_cart_v1',{}),{})
        self.add();key=next(iter(self.client.session['sunny_cart_v1']))
        self.client.post('/cart/',{'qty_'+key:'3','selected':[key]});self.assertEqual(self.client.session['sunny_cart_v1'][key]['qty'],3)
        self.client.post('/cart/',{'qty_'+key:'3'});self.assertEqual(len(self.client.get('/cart/checkout/').context['rows']),0)
        self.client.post('/cart/',{'qty_'+key:'3','remove':key});self.assertEqual(self.client.session['sunny_cart_v1'],{})
    def test_checkout_server_total_idempotency_session_privacy_and_price_change(self):
        order,body=self.cart_order();self.assertEqual(order.total,1200000)
        response=self.client.post('/cart/checkout/',{**body,'total':1});self.assertEqual(response.status_code,302);self.assertEqual(CartOrder.objects.count(),1)
        self.assertEqual(self.client.post('/cart/checkout/',{**body,'email':'else@example.test'}).status_code,200)
        url='/cart/orders/'+str(order.pk)+'/'
        self.assertEqual(Client().get(url).status_code,404);self.assertEqual(Client().get(url+'status/').status_code,404)
        self.assertEqual(self.client.get('/online/orders/'+str(order.lines.first().pk)+'/').status_code,404)
        self.add();form=self.client.get('/cart/checkout/').context['form'];OnlinePrice.objects.update(price=800000)
        self.assertEqual(self.client.post('/cart/checkout/',{**body,'request_id':str(form.initial['request_id']),'quote_token':form.initial['quote_token']}).status_code,200)
        self.assertEqual(CartOrder.objects.count(),1)
    def test_multiservice_payment_atomic_booking_totals_report_and_notification_once(self):
        service=Service.objects.create(title='Ba Na',slug='ba-na',ticket_id='eco',summary='x',body='x',published=True)
        OnlinePrice.objects.create(service=service,price=500000,starts_on=timezone.localdate())
        self.add(service,qty_default='1')
        order,body=self.cart_order();self.assertEqual(order.total,1700000);self.assertEqual(order.lines.count(),2)
        self.client.post('/cart/orders/'+str(order.pk)+'/');order.refresh_from_db();intent=order.intent
        self.assertEqual(self.hook(intent,transferAmount=1,id=500).json()['state'],'review');self.assertEqual(Workspace.objects.get(pk=1).data['bookings'],[])
        with self.captureOnCommitCallbacks(execute=True):self.assertEqual(self.hook(intent,transferAmount=1700000).json()['state'],'applied')
        rows=Workspace.objects.get(pk=1).data['bookings'];self.assertEqual(len(rows),2);self.assertEqual(sum(row['payments'][0]['amount'] for row in rows),1700000)
        self.assertEqual(self.hook(intent,transferAmount=1700000).json()['duplicate'],True)
        self.assertEqual(len(mail.outbox),1);self.assertEqual(mail.outbox[0].to,['admin@example.test'])
        self.client.force_login(self.admin);report=self.client.get('/api/reports/payment-methods/',{'source':'tickets','method':'bank_transfer'}).json();self.assertEqual(report['totals']['amount'],1700000);self.assertTrue(all(row['party']=='Digital' for row in report['rows']))
        self.assertContains(self.client.get('/online/staff/'),order.code)
    def test_upload_send_private_files_permissions_and_no_duplicate_mail(self):
        order=self.paid();url='/online/staff/cart/'+str(order.pk)+'/'
        other=User.objects.create_user('unprivileged',role='counter');self.client.force_login(other);self.assertEqual(self.client.get(url).status_code,403)
        self.client.force_login(self.admin)
        field=OrderTicket._meta.get_field('file');original=field.storage
        with tempfile.TemporaryDirectory() as folder:
            field.storage=FileSystemStorage(location=folder)
            try:
                raw=BytesIO();Image.new('RGB',(8,8),'white').save(raw,format='PNG')
                response=self.client.post(url,{'action':'upload','tickets':SimpleUploadedFile('ticket.png',raw.getvalue(),content_type='image/png')})
                self.assertEqual(response.status_code,302,response.content);ticket=OrderTicket.objects.get(order=order)
                self.assertTrue(ticket.file.storage.exists(ticket.file.name));self.assertFalse(ticket.file.path.startswith(str(__import__('django').conf.settings.MEDIA_ROOT)))
                self.client.logout();self.assertEqual(self.client.get('/online/staff/tickets/'+str(ticket.pk)+'/').status_code,302)
                self.client.force_login(self.admin);download=self.client.get('/online/staff/tickets/'+str(ticket.pk)+'/');self.assertEqual(download.status_code,200);download.close()
                before=len(mail.outbox);self.assertEqual(self.client.post(url,{'action':'send','confirmed':'on'}).status_code,302)
                order.refresh_from_db();self.assertEqual(order.email_state,'sent');self.assertEqual(len(mail.outbox),before+1);self.assertEqual(mail.outbox[-1].to,[order.email]);self.assertTrue(mail.outbox[-1].attachments)
                self.client.post(url,{'action':'send','confirmed':'on'});self.assertEqual(len(mail.outbox),before+1)
                self.assertNotContains(self.client.get('/online/staff/'),order.code)
            finally:field.storage=original
    def test_unpaid_invalid_attachment_external_and_email_failure(self):
        order,body=self.cart_order();self.client.post('/cart/orders/'+str(order.pk)+'/');order.refresh_from_db();self.client.force_login(self.admin);url='/online/staff/cart/'+str(order.pk)+'/'
        self.assertContains(self.client.post(url,{'action':'send','confirmed':'on'}),'Đơn chưa thanh toán')
        self.hook(order.intent)
        self.client.force_login(self.admin)
        response=self.client.post(url,{'action':'upload','tickets':SimpleUploadedFile('bad.pdf',b'%PDF-invalid')});self.assertContains(response,'PDF không hợp lệ');self.assertEqual(OrderTicket.objects.count(),0)
        self.assertContains(self.client.post(url,{'action':'external','confirmed':'on','note':'x'}),'ghi chú')
        response=self.client.post(url,{'action':'external','confirmed':'on','note':'Đã gửi bằng hộp thư công ty và kiểm tra địa chỉ đúng.'});self.assertEqual(response.status_code,302)
        order.refresh_from_db();self.assertEqual(order.email_state,'external');self.assertIsNotNone(order.emailed_at)
    def test_csrf_checkout_gate_and_expired_payment(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post('/services/hoi-an/add/',{}).status_code,403)
        self.add()
        with self.settings(ONLINE_CHECKOUT_ENABLED=False):self.assertContains(self.client.get('/cart/checkout/'),'disabled')
        order,body=self.cart_order();CartOrder.objects.filter(pk=order.pk).update(created_at=timezone.now()-timezone.timedelta(minutes=31))
        self.assertContains(self.client.post('/cart/orders/'+str(order.pk)+'/'),'hết hạn');self.assertEqual(SePayIntent.objects.count(),0)

    def test_mail_failure_reserves_state_and_requires_reconciliation(self):
        order=self.paid();self.client.force_login(self.admin);url='/online/staff/cart/'+str(order.pk)+'/'
        field=OrderTicket._meta.get_field('file');original=field.storage
        with tempfile.TemporaryDirectory() as folder:
            field.storage=FileSystemStorage(location=folder)
            try:
                raw=BytesIO();Image.new('RGB',(8,8),'white').save(raw,format='PNG')
                self.client.post(url,{'action':'upload','tickets':SimpleUploadedFile('ticket.png',raw.getvalue())})
                with patch('apps.online.fulfillment.EmailMessage.send',side_effect=RuntimeError('smtp timeout')) as send:
                    response=self.client.post(url,{'action':'send','confirmed':'on'})
                    self.assertContains(response,'không tự gửi lại')
                    order.refresh_from_db();self.assertEqual(order.email_state,'uncertain')
                    self.client.post(url,{'action':'send','confirmed':'on'});self.assertEqual(send.call_count,1)
                CartOrder.objects.filter(pk=order.pk).update(email_state='sending',send_started_at=timezone.now()-timezone.timedelta(minutes=6))
                order.refresh_from_db();self.assertTrue(order.can_reconcile)
                self.client.post(url,{'action':'external','confirmed':'on','note':'Đã đối chiếu hộp thư gửi; khách đã nhận đủ các vé.'})
                order.refresh_from_db();self.assertEqual(order.email_state,'external')
            finally:field.storage=original

    def test_notification_failure_does_not_undo_paid_order(self):
        order,body=self.cart_order();self.client.post('/cart/orders/'+str(order.pk)+'/');order.refresh_from_db()
        with patch('django.core.mail.EmailMessage.send',side_effect=RuntimeError('smtp unavailable')):
            with self.captureOnCommitCallbacks(execute=True):self.assertEqual(self.hook(order.intent).json()['state'],'applied')
        order.refresh_from_db();self.assertEqual(order.status,'paid');self.assertEqual(order.notification_state,'error');self.assertEqual(len(Workspace.objects.get(pk=1).data['bookings']),1)

    def test_buy_now_bypasses_cart_and_preserves_existing_items(self):
        self.add(qty_default='3');before=copy.deepcopy(self.client.session['sunny_cart_v1'])
        response=self.add(qty_default='1',purchase_mode='now')
        self.assertRedirects(response,'/checkout/now/',fetch_redirect_response=False)
        self.assertEqual(self.client.session['sunny_cart_v1'],before)
        response=self.client.get('/checkout/now/');self.assertEqual(response.context['total'],600000)
        form=response.context['form'];body={'request_id':str(form.initial['request_id']),'quote_token':form.initial['quote_token'],'customer_name':'Direct guest','email':'direct@example.test','phone_country':'+84','phone':'+84932548145','agreed':'on'}
        response=self.client.post('/checkout/now/',body)
        self.assertEqual(response.status_code,302,response.content)
        order=CartOrder.objects.get();self.assertEqual(order.total,600000);self.assertEqual(order.lines.count(),1)
        self.assertEqual(self.client.session['sunny_cart_v1'],before);self.assertEqual(self.client.session['sunny_direct_v1'],{})
        self.assertEqual(self.client.post('/checkout/now/',body).status_code,302);self.assertEqual(CartOrder.objects.count(),1)

    def test_card_price_auto_and_admin_selected_option(self):
        from .card_prices import attach_card_prices
        from django.core.exceptions import ValidationError
        option=ServiceOption.objects.create(service=self.service,title='ECO · Trẻ em',title_en='ECO · Child',ticket_id='eco')
        OnlinePrice.objects.create(service=self.service,option=option,price=300000,starts_on=timezone.localdate())
        row=attach_card_prices([self.service])[0];self.assertEqual(row.card_price,300000)
        response=self.client.get('/discover/');self.assertContains(response,'Giá từ');self.assertNotContains(response,'ECO · Trẻ em');self.assertNotContains(response,'Tùy ngày sử dụng')
        self.service.card_price_source='default';self.service.save();self.assertEqual(attach_card_prices([self.service])[0].card_price,600000)
        premium=ServiceOption.objects.create(service=self.service,title='HIGH · Người lớn',title_en='HIGH · Adult',ticket_id='eco')
        OnlinePrice.objects.create(service=self.service,option=premium,price=700000,starts_on=timezone.localdate())
        self.service.card_price_source='option';self.service.card_price_option=premium;self.service.full_clean();self.service.save()
        self.assertEqual(attach_card_prices([self.service])[0].card_price,700000)
        response=self.client.get('/services/',{'lang':'en'});self.assertContains(response,'From');self.assertContains(response,'700,000');self.assertNotContains(response,'HIGH · Adult');self.assertNotContains(response,'Varies by visit date')
        other=Service.objects.create(title='Other',slug='other-card',ticket_id='eco',summary='x',body='x')
        self.service.card_price_option=ServiceOption.objects.create(service=other,title='Other',ticket_id='eco')
        with self.assertRaises(ValidationError):self.service.full_clean()

    def test_card_price_hides_unavailable_and_uses_future_bookable_window(self):
        from .card_prices import attach_card_prices
        OnlinePrice.objects.update(ends_on=timezone.localdate()-timezone.timedelta(days=1))
        self.assertIsNone(attach_card_prices([self.service])[0].card_price)
        future=timezone.localdate()+timezone.timedelta(days=8)
        OnlinePrice.objects.create(service=self.service,price=450000,starts_on=future)
        self.assertEqual(attach_card_prices([self.service])[0].card_price,450000)
        obj=Workspace.objects.get(pk=1);obj.data['costPrices'][0]['from']=(future+timezone.timedelta(days=1)).isoformat();obj.save()
        self.assertEqual(attach_card_prices([self.service])[0].card_price,450000)
        obj.data['ticketTypes'][0]['active']=False;obj.save()
        self.assertIsNone(attach_card_prices([self.service])[0].card_price)

    def test_existing_online_bookings_migrate_to_digital_without_financial_changes(self):
        import importlib
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        obj=Workspace.objects.get(pk=1)
        online={'id':'old-online','salesChannel':'online','agent':'Khách online','customerType':'retail','customerName':'Actual guest','customerEmail':'guest@example.test','revenue':500000,'payments':[{'id':'bank-event','amount':500000,'method':'bank_transfer'}],'counterVersion':1}
        manual={'id':'manual','agent':'Some agency','customerName':'Manual guest','revenue':300000}
        obj.data['bookings']=[online,manual];obj.save();revision=obj.revision
        migration=importlib.import_module('apps.online.migrations.0009_online_digital_party')
        migration.mark_digital(apps,SimpleNamespace(connection=connection));obj.refresh_from_db()
        self.assertEqual(obj.data['bookings'][0],{**online,'agent':'Digital'});self.assertEqual(obj.data['bookings'][1],manual);self.assertEqual(obj.revision,revision+1)
        migration.mark_digital(apps,SimpleNamespace(connection=connection));obj.refresh_from_db();self.assertEqual(obj.revision,revision+1)
        from apps.legacy.payment_methods import source_rows
        self.assertEqual(list(source_rows('tickets'))[0]['party'],'Digital')

    def test_ticket_type_groups_have_separate_audience_prices_and_quantities(self):
        from .cart import ticket_groups
        from django.core.exceptions import ValidationError
        self.service.ticket_id='';self.service.save()
        options=[]
        for audience,title,price in [('adult','ECO · Người lớn',540000),('child','ECO · Trẻ em',270000),('senior','ECO · Người cao tuổi',400000)]:
            option=ServiceOption.objects.create(service=self.service,title=title,ticket_id='eco',group_name='ECO',group_name_en='ECO',audience=audience)
            OnlinePrice.objects.create(service=self.service,option=option,price=price,starts_on=timezone.localdate());options.append(option)
        groups=ticket_groups(self.service);self.assertEqual(len(groups),1);self.assertEqual([row['title'] for row in groups[0]['options']],['Người lớn','Trẻ em','Người cao tuổi'])
        response=self.client.get('/services/hoi-an/');self.assertContains(response,'class="ticket-group"',count=1);self.assertContains(response,'Người cao tuổi')
        english=self.client.get('/services/hoi-an/',{'lang':'en'});self.assertContains(english,'Senior')
        response=self.add(qty_default='0',**{'qty_'+str(options[0].pk):'1','qty_'+str(options[1].pk):'2'});self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/cart/').context['total'],1080000)
        duplicate=ServiceOption(service=self.service,title='Duplicate adult',ticket_id='eco',group_name='eco',audience='adult')
        with self.assertRaises(ValidationError):duplicate.full_clean()

    def test_legacy_option_names_group_without_price_or_id_changes(self):
        import importlib
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        adult=ServiceOption.objects.create(service=self.service,title='Eco NL',ticket_id='eco')
        child=ServiceOption.objects.create(service=self.service,title='Eco TE',ticket_id='eco')
        senior=ServiceOption.objects.create(service=self.service,title='High NCT',ticket_id='eco')
        unknown=ServiceOption.objects.create(service=self.service,title='Custom package',ticket_id='eco')
        price=OnlinePrice.objects.create(service=self.service,option=adult,price=540000,starts_on=self.day)
        migration=importlib.import_module('apps.online.migrations.0010_ticket_groups_audiences');migration.group_existing_options(apps,SimpleNamespace(connection=connection))
        adult.refresh_from_db();child.refresh_from_db();senior.refresh_from_db();unknown.refresh_from_db();price.refresh_from_db()
        self.assertEqual((adult.group_name,adult.audience,adult.title),('Eco','adult','Eco NL'));self.assertEqual((child.group_name,child.audience),('Eco','child'));self.assertEqual((senior.group_name,senior.audience),('High','senior'));self.assertEqual(unknown.group_name,'');self.assertEqual(price.option_id,adult.pk);self.assertEqual(price.price,540000)
