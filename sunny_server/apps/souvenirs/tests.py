from datetime import timedelta
from io import BytesIO
import json
import tempfile
import uuid
from PIL import Image
import zxingcpp
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase,Client,override_settings
from django.utils import timezone
from apps.accounts.models import User
from apps.legacy.models import Workspace,CardFeeRate
from apps.legacy.card_fees import references
from .models import Product,Asset,Article,SaleOrder

@override_settings(SOUVENIRS_ENABLED=True,SOUVENIRS_PUBLIC_ORIGIN='https://souvenirs.test',ALLOWED_HOSTS=['testserver','souvenirs.test'])
class SouvenirsTests(TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.settings_context=override_settings(MEDIA_ROOT=self.folder.name);self.settings_context.enable();self.addCleanup(self.settings_context.disable)
        self.user=User.objects.create_user('shop-staff',role='counter');self.user.user_permissions.add(Permission.objects.get(content_type__app_label='souvenirs',codename='sell'));self.client.force_login(self.user)
        self.admin=User.objects.create_superuser('shop-admin',password='test-password',role='admin')
        Workspace.objects.create(pk=1,data={'bookings':[{'id':'TICKET-KEEP','revenue':999}],'agents':[]})
        self.product=Product.objects.create(sku='SV001',name='Đèn lồng Hội An',summary='Một câu chuyện nhỏ',story='Bàn tay người thợ.\n<script>alert(1)</script>',price=100000,cost=40000,published=True)

    def post(self,url,body):return self.client.post(url,json.dumps(body),content_type='application/json')
    def create(self,**changes):return self.post('/souvenirs/api/sales/',{'requestId':str(uuid.uuid4()),'items':[{'product':str(self.product.pk),'quantity':2,'expectedPrice':100000}],'note':'Quà mang về',**changes})
    def order(self):
        response=self.create();self.assertEqual(response.status_code,201,response.content);return response.json()['order']
    def action(self,order,**values):return self.post('/souvenirs/api/orders/'+order['id']+'/',values)
    def png(self):
        image=Image.new('RGB',(30,40),'#327b6c');stream=BytesIO();image.save(stream,format='PNG');return SimpleUploadedFile('lantern.png',stream.getvalue(),content_type='image/png')

    def test_public_catalog_product_story_articles_and_hidden_cost(self):
        Article.objects.create(product=self.product,title='Nghề thủ công',body='Dòng chữ cho khách xem')
        guest=Client();response=guest.get('/souvenirs/catalog/');self.assertContains(response,self.product.name);self.assertNotContains(response,'40000')
        self.assertContains(guest.get('/souvenirs/catalog/',{'q':'den long'}),self.product.name)
        response=guest.get('/souvenirs/p/'+self.product.slug+'/');self.assertContains(response,'Nghề thủ công');self.assertContains(response,'&lt;script&gt;');self.assertNotContains(response,'<script>alert(1)</script>');self.assertNotContains(response,'Giá vốn')
        self.product.published=False;self.product.save();self.assertEqual(guest.get('/souvenirs/p/'+self.product.slug+'/').status_code,404)

    def test_public_subdomain_routing_has_no_admin_or_sales_endpoints(self):
        guest=Client();self.assertContains(guest.get('/',HTTP_HOST='souvenirs.test'),self.product.name)
        self.assertEqual(guest.get('/p/'+self.product.slug+'/',HTTP_HOST='souvenirs.test').status_code,200)
        self.assertEqual(guest.get('/souvenirs/manage/',HTTP_HOST='souvenirs.test').status_code,404);self.assertEqual(guest.get('/admin/',HTTP_HOST='souvenirs.test').status_code,404)

    def test_feature_disabled_does_not_publish_new_module(self):
        with override_settings(SOUVENIRS_ENABLED=False):
            self.assertEqual(self.client.get('/souvenirs/manage/').status_code,404);self.assertEqual(Client().get('/souvenirs/catalog/').status_code,404)

    def test_assets_publish_only_when_product_public_and_support_range(self):
        image=Asset.objects.create(product=self.product,kind='image',file=self.png());guest=Client();url='/souvenirs/assets/'+str(image.pk)+'/'
        response=guest.get(url);self.assertEqual(response.status_code,200);response.close();response=guest.get(url,HTTP_RANGE='bytes=0-9');self.assertEqual(response.status_code,206);self.assertEqual(len(b''.join(response.streaming_content)),10);response.close()
        self.assertEqual(guest.get(url,HTTP_RANGE='bytes=999999-').status_code,416)
        self.product.published=False;self.product.save();self.assertEqual(guest.get(url).status_code,404)
        self.client.force_login(self.admin);response=self.client.get(url);self.assertEqual(response.status_code,200);response.close()

    def test_staff_menu_management_permissions_and_private_data(self):
        self.assertRedirects(self.client.get('/'),'/souvenirs/manage/',fetch_redirect_response=False)
        self.assertContains(self.client.get('/souvenirs/manage/'),'Bán hàng lưu niệm')
        self.assertEqual(self.client.get('/souvenirs/products/new/').status_code,403)
        self.assertEqual(self.client.get('/souvenirs/api/report/').status_code,403)
        response=self.client.get('/souvenirs/api/sales/');self.assertNotContains(response,'cost');self.assertNotContains(response,'40000')
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user);self.assertEqual(csrf.post('/souvenirs/api/sales/','{}',content_type='application/json').status_code,403)

    def test_product_form_upload_article_and_durable_qr(self):
        self.client.force_login(self.admin)
        data={'sku':'SV002','name':'Túi vải Hội An','category':'Dệt','price':'200000','cost':'50000','summary':'Từ Hội An','story':'Dệt nên ký ức','published':'on','sort_order':0,'expected_version':1,'assets-TOTAL_FORMS':1,'assets-INITIAL_FORMS':0,'assets-MIN_NUM_FORMS':0,'assets-MAX_NUM_FORMS':30,'assets-0-kind':'image','assets-0-file':self.png(),'assets-0-caption':'Túi vải','assets-0-position':0,'articles-TOTAL_FORMS':1,'articles-INITIAL_FORMS':0,'articles-MIN_NUM_FORMS':0,'articles-MAX_NUM_FORMS':30,'articles-0-title':'Câu chuyện làng nghề','articles-0-body':'Nội dung đầy đủ','articles-0-position':0}
        response=self.client.post('/souvenirs/products/new/',data);self.assertEqual(response.status_code,302,response.content[:1000]);p=Product.objects.get(sku='SV002');self.assertEqual(p.assets.count(),1);self.assertEqual(p.articles.count(),1)
        response=self.client.get('/souvenirs/products/'+str(p.pk)+'/label/?format=png');self.assertEqual(response.status_code,200);decoded=zxingcpp.read_barcode(Image.open(BytesIO(response.content)));self.assertEqual(decoded.text,'https://sn.hoianmemorieslands.com/souvenirs/p/'+p.slug+'/')
        old_slug=p.slug;p.name='Tên mới';p.save();self.assertEqual(Product.objects.get(pk=p.pk).slug,old_slug)

    def test_bad_image_cannot_be_published_as_product_media(self):
        from .forms import AssetForm
        form=AssetForm({'kind':'image','position':0},{'file':SimpleUploadedFile('evil.png',b'<script>evil</script>',content_type='image/png')});self.assertFalse(form.is_valid())

    def test_create_prices_snapshots_retry_and_no_ticket_data_change(self):
        before=Workspace.objects.get(pk=1).data;request_id=str(uuid.uuid4());first=self.create(requestId=request_id);self.assertEqual(first.status_code,201,first.content)
        again=self.create(requestId=request_id);self.assertTrue(again.json()['duplicate']);self.assertEqual(SaleOrder.objects.count(),1);self.assertEqual(again.json()['order']['total'],200000)
        self.assertEqual(Workspace.objects.get(pk=1).data,before);self.product.price=150000;self.product.name='Đèn lồng mới';self.product.save()
        order=SaleOrder.objects.get();line=order.lines.get();self.assertEqual(line.name,'Đèn lồng Hội An');self.assertEqual(line.unit_price,100000);self.assertEqual(order.total,200000)
        self.assertEqual(self.create().status_code,400)
        self.assertEqual(self.create(requestId=request_id,note='Khác').status_code,400)

    def test_invalid_items_and_unpublished_product_rejected(self):
        for qty in (0,-1,True,1.5,10001):self.assertEqual(self.create(items=[{'product':str(self.product.pk),'quantity':qty,'expectedPrice':100000}]).status_code,400)
        self.assertEqual(self.create(items=[]).status_code,400)
        self.product.published=False;self.product.save();self.assertEqual(self.create().status_code,400);self.assertEqual(SaleOrder.objects.count(),0)

    def test_paid_once_revenue_filters_and_cancellation_rules(self):
        order=self.order();self.client.force_login(self.admin);self.assertEqual(self.client.get('/souvenirs/api/report/').json()['totals']['total'],0);self.client.force_login(self.user)
        self.assertEqual(self.action(order,action='pay',method='cash',confirmed=False).status_code,400)
        response=self.action(order,action='pay',method='cash',confirmed=True);self.assertEqual(response.status_code,200,response.content);self.assertTrue(self.action(order,action='pay',method='cash',confirmed=True).json()['duplicate'])
        self.assertEqual(self.action(order,action='pay',method='bank_transfer',confirmed=True).status_code,400);self.assertEqual(self.action(order,action='cancel',confirmed=True).status_code,400)
        self.client.force_login(self.admin);report=self.client.get('/souvenirs/api/report/').json();self.assertEqual(report['totals']['total'],200000);self.assertEqual(report['totals']['quantity'],2);self.assertEqual(report['totals']['profit'],120000)
        future=(timezone.localdate()+timedelta(days=1)).isoformat();self.assertEqual(self.client.get('/souvenirs/api/report/',{'from':future}).json()['totals']['total'],0)
        self.assertEqual(self.client.get('/souvenirs/api/report/',{'from':'2026-12-31','to':'2026-01-01'}).status_code,400)

    def test_card_fee_snapshots_share_management_and_remain_historical(self):
        rate=CardFeeRate.objects.create(scheme='visa',origin='domestic',rate='2.55',starts_on=timezone.localdate());order=self.order()
        self.assertEqual(self.action(order,action='pay',method='card',confirmed=True).status_code,400)
        quote=self.action(order,action='quote',scheme='visa',origin='domestic').json()['quote'];self.assertEqual(quote['feeAmount'],5100)
        self.assertEqual(self.action(order,action='pay',method='card',confirmed=True,cardFeeQuote={**quote,'feeAmount':0}).status_code,409)
        self.assertEqual(self.action(order,action='pay',method='card',confirmed=True,cardFeeQuote=quote).status_code,200);self.assertEqual(references(rate.pk)[0]['feeAmount'],5100)
        self.client.force_login(self.admin);report=self.client.get('/souvenirs/api/report/').json();self.assertEqual(report['totals']['net'],194900);self.assertEqual(report['totals']['profit'],114900)

    def test_staff_cannot_read_or_pay_others_order(self):
        order=self.order();other=User.objects.create_user('other-souvenir',role='counter');other.user_permissions.add(Permission.objects.get(content_type__app_label='souvenirs',codename='sell'));self.client.force_login(other)
        self.assertEqual(self.client.get('/souvenirs/api/sales/').json()['orders'],[]);self.assertEqual(self.action(order,action='pay',method='cash',confirmed=True).status_code,404)

    def test_cancelled_order_has_no_revenue_and_cannot_be_paid(self):
        order=self.order();self.assertEqual(self.action(order,action='cancel',confirmed=True).status_code,200);self.assertEqual(self.action(order,action='pay',method='cash',confirmed=True).status_code,400)
        self.client.force_login(self.admin);self.assertEqual(self.client.get('/souvenirs/api/report/').json()['totals']['total'],0)

    def test_bilingual_content_switch_search_fallback_and_escaping(self):
        self.product.name_en='Hoi An lantern';self.product.category='Thủ công';self.product.category_en='Crafts';self.product.story_en='Handmade <script>bad()</script>';self.product.save()
        Article.objects.create(product=self.product,title='Tiêu đề',body='Nội dung',title_en='Craft story',body_en='English article')
        guest=Client()
        response=guest.get('/souvenirs/catalog/',{'lang':'en','q':'lantern','category':'Thủ công'})
        self.assertContains(response,'Hoi An lantern');self.assertContains(response,'Crafts');self.assertContains(response,'lang=en');self.assertContains(response,'Find a gift')
        response=guest.get('/souvenirs/p/'+self.product.slug+'/',{'lang':'en'})
        self.assertContains(response,'lang="en"');self.assertContains(response,'Craft story');self.assertContains(response,'English article');self.assertContains(response,'&lt;script&gt;');self.assertContains(response,self.product.summary)
        self.assertNotContains(response,'<script>bad()</script>')
        response=guest.get('/souvenirs/p/'+self.product.slug+'/',{'lang':'vi'})
        self.assertContains(response,self.product.name);self.assertNotContains(response,'English article')
        self.assertContains(guest.get('/souvenirs/catalog/',{'lang':'invalid'}),'lang="vi"')
        self.client.force_login(self.admin)
        response=self.client.get('/souvenirs/products/'+str(self.product.pk)+'/edit/')
        self.assertContains(response,'name="name_en"');self.assertContains(response,'name="articles-0-title_en"')

    def test_product_qr_does_not_use_retired_subdomain_or_require_login(self):
        self.client.force_login(self.admin)
        response=self.client.get('/souvenirs/products/'+str(self.product.pk)+'/label/?format=png')
        decoded=zxingcpp.read_barcode(Image.open(BytesIO(response.content)))
        self.assertEqual(decoded.text,'https://sn.hoianmemorieslands.com/souvenirs/p/'+self.product.slug+'/')
        guest=Client();response=guest.get('/souvenirs/p/'+self.product.slug+'/')
        self.assertEqual(response.status_code,200);self.assertContains(response,self.product.name)
        other=Product.objects.create(sku='OTHER',name='Other product',price=50000,published=True)
        response=self.client.get('/souvenirs/products/'+str(other.pk)+'/label/?format=png')
        other_qr=zxingcpp.read_barcode(Image.open(BytesIO(response.content)))
        self.assertNotEqual(decoded.text,other_qr.text)
        self.assertEqual(other_qr.text,'https://sn.hoianmemorieslands.com/souvenirs/p/'+other.slug+'/')
        self.assertEqual(guest.get('/admin/').status_code,302)

    def test_intro_video_first_without_duplicate_and_bilingual_button(self):
        first=Asset.objects.create(product=self.product,kind='video',file='souvenirs/intro.mp4',position=1)
        second=Asset.objects.create(product=self.product,kind='video',file='souvenirs/extra.mp4',position=2)
        guest=Client();response=guest.get('/souvenirs/p/'+self.product.slug+'/',{'lang':'en'})
        html=response.content.decode()
        self.assertContains(response,'Listen to the introduction');self.assertContains(response,'id="svIntroVideo"')
        self.assertEqual(html.count('/assets/'+str(first.pk)+'/'),1)
        self.assertEqual(html.count('/assets/'+str(second.pk)+'/'),1)
        self.assertLess(html.index('id="svIntroVideo"'),html.index('class="sv-product-intro"'))
        self.assertContains(guest.get('/souvenirs/p/'+self.product.slug+'/',{'lang':'vi'}),'Nghe giới thiệu')
        Asset.objects.all().delete()
        self.assertNotContains(guest.get('/souvenirs/p/'+self.product.slug+'/'),'souvenirs_video.js')

    def test_language_detection_english_default_browser_preference_and_manual_choice(self):
        url='/souvenirs/p/'+self.product.slug+'/'
        for header,expected in [('', 'en'),('vi-VN,vi;q=0.9,en;q=0.8','vi'),('en-US,en;q=0.9,vi;q=0.5','en'),('fr-FR,vi;q=0.4','en'),('en;q=0.4,vi-VN;q=0.9','vi'),('*','en'),('vi;q=0,en;q=1','en'),('not a valid header','en')]:
            with self.subTest(header=header):
                response=Client().get(url,HTTP_ACCEPT_LANGUAGE=header)
                self.assertEqual(response['Content-Language'],expected)
                self.assertContains(response,'lang="'+expected+'"')
                self.assertIn('Accept-Language',response['Vary'])
        guest=Client();response=guest.get(url,{'lang':'vi'},HTTP_ACCEPT_LANGUAGE='en-US')
        self.assertEqual(response['Content-Language'],'vi');self.assertEqual(response.cookies['souvenirs_lang'].value,'vi')
        self.assertEqual(guest.get('/souvenirs/catalog/',HTTP_ACCEPT_LANGUAGE='en-US')['Content-Language'],'vi')
        self.assertEqual(guest.get(url,{'lang':'en'},HTTP_ACCEPT_LANGUAGE='vi-VN')['Content-Language'],'en')
        self.assertEqual(guest.get(url,HTTP_ACCEPT_LANGUAGE='vi-VN')['Content-Language'],'en')
        self.assertEqual(Client().get(url,{'lang':'invalid'})['Content-Language'],'en')

    def edit_body(self,order,**changes):
        return {'action':'edit','revision':order.get('revision',0),'confirmed':True,'reason':'Sửa nhập nhầm','note':'Ghi chú mới','items':[{'product':str(self.product.pk),'quantity':3,'unitPrice':110000}],**changes}

    def test_order_edit_delete_permissions_and_admin_default(self):
        order=self.order()
        self.assertEqual(self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order)).status_code,403)
        self.assertEqual(self.action(order,action='delete',revision=0,confirmed=True,reason='Nhập nhầm').status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='souvenirs',codename='edit_orders'))
        response=self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order));self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['order']['total'],330000)
        self.assertEqual(self.action(order,action='delete',revision=1,confirmed=True,reason='Nhập nhầm').status_code,403)
        manager=User.objects.create_user('role-admin',role='admin');self.client.force_login(manager)
        data=self.client.get('/souvenirs/api/sales/').json();self.assertTrue(data['canEdit']);self.assertTrue(data['canDelete']);self.assertEqual(data['orders'][0]['id'],order['id'])
        self.assertEqual(self.action(order,action='delete',revision=1,confirmed=True,reason='Nhập nhầm').status_code,200)
        obj=SaleOrder.objects.get(pk=order['id']);self.assertIsNotNone(obj.deleted_at);self.assertEqual(len(obj.history),2)
        self.assertEqual(self.client.get('/souvenirs/api/sales/').json()['orders'],[])
        self.assertEqual(self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order)).status_code,409)

    def test_paid_order_edit_report_cost_snapshot_and_soft_delete(self):
        order=self.order();self.action(order,action='pay',method='cash',confirmed=True)
        self.client.force_login(self.admin);obj=SaleOrder.objects.get(pk=order['id']);created=obj.created_at;paid=obj.paid_at
        self.product.cost=99999;self.product.save()
        response=self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order,revision=1));self.assertEqual(response.status_code,200,response.content)
        totals=self.client.get('/souvenirs/api/report/').json()['totals'];self.assertEqual(totals['total'],330000);self.assertEqual(totals['cost'],120000)
        obj.refresh_from_db();self.assertEqual(obj.created_at,created);self.assertEqual(obj.paid_at,paid);self.assertEqual(obj.revision,2)
        self.assertEqual(obj.history[0]['before']['total'],200000)
        response=self.action(order,action='delete',revision=2,confirmed=True,reason='Đối soát hủy');self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.get('/souvenirs/api/report/').json()['totals']['total'],0)
        self.assertEqual(Workspace.objects.get(pk=1).data['bookings'][0]['id'],'TICKET-KEEP')

    def test_edit_uses_historical_card_rate_and_stale_revision_rejected(self):
        rate=CardFeeRate.objects.create(scheme='visa',origin='domestic',rate='2.55',starts_on=timezone.localdate());order=self.order()
        quote=self.action(order,action='quote',scheme='visa',origin='domestic').json()['quote'];self.action(order,action='pay',method='card',confirmed=True,cardFeeQuote=quote)
        self.client.force_login(self.admin)
        self.assertEqual(self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order)).status_code,409)
        rate.active=False;rate.save()
        response=self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order,revision=1));self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['order']['fee'],8415);self.assertEqual(response.json()['order']['net'],321585)
        self.assertEqual(self.action(order,action='delete',revision=1,confirmed=True,reason='stale').status_code,409)

    def test_editor_without_sell_only_own_orders_and_invalid_changes_rollback(self):
        order=self.order();other=User.objects.create_user('other-editor',role='counter');other.user_permissions.add(Permission.objects.get(content_type__app_label='souvenirs',codename='edit_orders'));self.client.force_login(other)
        self.assertEqual(self.client.get('/souvenirs/manage/').status_code,200)
        self.assertEqual(self.client.get('/souvenirs/api/sales/').json()['orders'],[])
        self.assertEqual(self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order)).status_code,404)
        self.client.force_login(self.admin)
        for change in ({'reason':''},{'items':[]},{'items':[{'product':str(self.product.pk),'quantity':-1,'unitPrice':10}]},{'items':[{'product':str(self.product.pk),'quantity':1,'unitPrice':'NaN'}]}):
            self.assertEqual(self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order,**change)).status_code,400)
        obj=SaleOrder.objects.get(pk=order['id']);self.assertEqual(obj.total,200000);self.assertEqual(obj.revision,0);self.assertEqual(obj.lines.count(),1)

    def test_operator_full_workspace_does_not_grant_order_edit_delete(self):
        operator=User.objects.create_user('full-operator',role='operator')
        operator.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='workspace__full_access'))
        self.client.force_login(operator);data=self.client.get('/souvenirs/api/sales/').json()
        self.assertFalse(data['canEdit']);self.assertFalse(data['canDelete'])

    def test_stale_cashier_cannot_confirm_changed_order_without_revision(self):
        order=self.order();self.client.force_login(self.admin)
        self.post('/souvenirs/api/orders/'+order['id']+'/',self.edit_body(order))
        self.client.force_login(self.user)
        self.assertEqual(self.action(order,action='pay',method='cash',confirmed=True).status_code,409)
        self.assertEqual(self.action(order,action='pay',method='cash',confirmed=True,revision=1).status_code,200)
