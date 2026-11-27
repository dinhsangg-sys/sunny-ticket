"""Isolated render fixtures. Never opens the business database or sends real email."""
import os,json,tempfile
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.test import Client
from django.utils import timezone
from apps.accounts.models import User
from apps.legacy.models import Workspace
from apps.online.models import Service,Article,OnlinePrice
with tempfile.TemporaryDirectory() as folder:
    settings.DATABASES['default']['NAME']=str(Path(folder)/'preview.sqlite3');settings.MEDIA_ROOT=Path(folder)/'media'
    settings.ALLOWED_HOSTS=['testserver','sunnygovn.com'];settings.SOUVENIRS_ENABLED=True;settings.ONLINE_CHECKOUT_ENABLED=True;settings.ONLINE_PAYMENT_OWNER='preview-admin';settings.COUNTER_EMAIL_ENABLED=True;settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend';settings.DEFAULT_FROM_EMAIL='preview@example.test'
    settings.SEPAY_ENABLED=True;settings.SEPAY_MODE='test';settings.SEPAY_WEBHOOK_SECRET='preview-only-secret-01234567890123456789';settings.SEPAY_BANK_CODE='TestBank';settings.SEPAY_GATEWAY='Test Bank';settings.SEPAY_ACCOUNT_NUMBER='0123456789';settings.SEPAY_ACCOUNT_NAME='SUNNY TEST'
    call_command('migrate',verbosity=0)
    admin=User.objects.create_superuser('preview-admin',password='preview-only-password',role='admin')
    Workspace.objects.create(pk=1,data={'ticketTypes':[{'id':'eco','name':'Eco','product':'Hội An','active':True}],'suppliers':[{'id':'s','name':'Hidden supplier','active':True}],'costPrices':[{'id':'cost','ticketId':'eco','supplierId':'s','price':400000,'from':'2020-01-01','isDefault':True}],'bookings':[]})
    service=Service.objects.create(title='Một buổi tối đáng nhớ ở Hội An',slug='hoi-an',ticket_id='eco',summary='Chậm lại một nhịp để cảm nhận vẻ đẹp của phố Hội qua một trải nghiệm được chuẩn bị chu đáo.',body='Đọc kỹ ngày sử dụng và thông tin vé trước khi đặt. Đây là nội dung thử giao diện, không phải dịch vụ đang mở bán.',published=True,title_en='An evening to remember in Hoi An',summary_en='Slow down and discover the charm of Hoi An through a thoughtfully planned local experience.',body_en='Read your ticket conditions and visit date before booking. This is a layout fixture, not a live offer.')
    OnlinePrice.objects.create(service=service,price=600000,starts_on=timezone.localdate())
    Article.objects.create(title='Đi chậm một chút, thấy Hội An nhiều hơn',slug='di-cham',summary='Từ những con ngõ nhỏ đến nhịp sống ven sông, một góc nhìn để bắt đầu hành trình của bạn.',body='Bài viết thử bố cục. Không xuất bản lên website thật.',published=True)

    from apps.online.models import ServiceTicketGroup,ServiceOption
    group=ServiceTicketGroup.objects.create(service=service,name='ECO',name_en='ECO')
    ServiceOption.objects.create(service=service,group=group,group_name='ECO',audience='adult',title='ECO adult',ticket_id='eco',online_price=540000,published_price=600000,strike_published_price=True)
    user=Client();user.force_login(admin)
    output={'service':user.get('/admin/online/service/'+str(service.pk)+'/change/').content.decode(),'group':user.get('/admin/online/serviceticketgroup/'+str(group.pk)+'/change/').content.decode(),'public':user.get('/services/hoi-an/?lang=vi').content.decode(),'prices':user.get('/services/hoi-an/prices/',{'date':str(timezone.localdate())}).json()}
    output['i18n']=user.get('/admin/jsi18n/').content.decode()
    connections.close_all()
    print(json.dumps(output))
