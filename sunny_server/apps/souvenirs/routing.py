from urllib.parse import urlparse
from django.conf import settings

def context(request):return {'souvenirs_enabled':settings.SOUVENIRS_ENABLED}

class PublicHostMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        host=request.get_host().split(':')[0].lower()
        if settings.SOUVENIRS_ENABLED and host==urlparse(settings.SOUVENIRS_PUBLIC_ORIGIN).hostname:request.urlconf='apps.souvenirs.public_urls'
        return self.get_response(request)
