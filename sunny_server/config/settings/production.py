from .base import *
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DATABASES = {'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.environ['POSTGRES_DB'],'USER':os.environ['POSTGRES_USER'],'PASSWORD':os.environ['POSTGRES_PASSWORD'],'HOST':os.environ.get('POSTGRES_HOST','127.0.0.1'),'PORT':os.environ.get('POSTGRES_PORT','5432')}}
MEDIA_ROOT = Path(os.environ.get('SUNNY_MEDIA_ROOT','/var/lib/sunny/media'))
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
SECURE_HSTS_SECONDS = 3600
