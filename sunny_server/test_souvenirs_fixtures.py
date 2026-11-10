"""Render real templates using a temporary database/media tree, never business data."""
import base64,json,os,tempfile
from pathlib import Path
from io import BytesIO
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.db import connections
from django.test import Client
from django.utils import timezone
from apps.accounts.models import User
from apps.souvenirs.models import Product,Asset,Article
from PIL import Image

with tempfile.TemporaryDirectory() as folder:
    settings.DATABASES['default']['NAME']=str(Path(folder)/'preview.sqlite3');settings.MEDIA_ROOT=Path(folder)/'media';settings.SOUVENIRS_ENABLED=True;settings.SOUVENIRS_PUBLIC_ORIGIN='https://souvenirs.test';settings.ALLOWED_HOSTS=['testserver','souvenirs.test']
    call_command('migrate',verbosity=0)
    user=User.objects.create_user('preview-manager',is_superuser=True,is_staff=True,role='admin')
    p=Product.objects.create(sku='SV001',name='Đèn lồng Hội An',price=150000,cost=50000,published=True,category='Nét thủ công',summary='Một món quà nhỏ lưu giữ sắc màu phố Hội.',story='Những nếp vải và bàn tay người thợ.\nMột câu chuyện để mang về từ Hội An.')
    stream=BytesIO();Image.new('RGB',(600,750),'#c4b393').save(stream,format='PNG');raw=stream.getvalue();asset=Asset(product=p,kind='image',caption='Ảnh thử bố cục');asset.file.save('preview.png',ContentFile(raw),save=True)
    Article.objects.create(product=p,title='Nghề thủ công và những ký ức',body='Mỗi sản phẩm gói ghém một chút phố Hội.')
    guest=Client(HTTP_ACCEPT_LANGUAGE="vi-VN,vi;q=0.9");staff=Client();staff.force_login(user)
    output={'product':{'id':str(p.pk),'slug':p.slug,'sku':p.sku,'name':p.name,'price':150000},'image':base64.b64encode(raw).decode(),'today':timezone.localdate().isoformat()}
    for name,response in [('catalog',guest.get('/',HTTP_HOST='souvenirs.test')),('detail',guest.get('/p/'+p.slug+'/',HTTP_HOST='souvenirs.test')),('manage',staff.get('/souvenirs/manage/')),('edit',staff.get('/souvenirs/products/'+str(p.pk)+'/edit/'))]:
        assert response.status_code==200;(output.__setitem__(name,response.content.decode()))
    Asset.objects.create(product=p,kind='video',file='souvenirs/intro.mp4',caption='Giới thiệu',position=0)
    output['video_detail']=guest.get('/p/'+p.slug+'/',HTTP_HOST='souvenirs.test').content.decode()
    connections.close_all()
    print(json.dumps(output))
