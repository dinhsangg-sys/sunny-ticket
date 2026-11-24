from urllib.parse import urlparse
HOSTS={
 'facebook_url':{'facebook.com','www.facebook.com','m.facebook.com','fb.com','www.fb.com','fb.me'},
 'tiktok_url':{'tiktok.com','www.tiktok.com','vm.tiktok.com','vt.tiktok.com'},
 'google_maps_url':{'google.com','www.google.com','maps.google.com','maps.app.goo.gl','goo.gl'},
 'whatsapp_url':{'wa.me','api.whatsapp.com','www.whatsapp.com','whatsapp.com'},
 'zalo_url':{'zalo.me','www.zalo.me','oa.zalo.me'},
 'line_url':{'line.me','www.line.me','lin.ee'},
}
def valid_contact_url(field,value):
    try:
        url=urlparse(value)
        if url.scheme!='https' or url.hostname not in HOSTS[field] or url.username or url.password or url.port not in (None,443) or any(c.isspace() or ord(c)<32 for c in value):return False
        if field=='google_maps_url' and url.hostname in ('google.com','www.google.com','goo.gl') and not url.path.startswith('/maps'):return False
        return bool(url.path.strip('/')) or bool(url.query)
    except (ValueError,KeyError,TypeError):return False

def public_contacts():
    from .models import SiteContact
    obj=SiteContact.objects.filter(pk=1).first()
    social=[];contacts=[];line_phone=''
    if obj:
        for field,label,target in [('facebook_url','Facebook',social),('tiktok_url','TikTok',social),('google_maps_url','Google Maps',social),('whatsapp_url','WhatsApp',contacts),('zalo_url','Zalo',contacts),('line_url','LINE',contacts)]:
            value=getattr(obj,field)
            if value and valid_contact_url(field,value):target.append({'label':label,'url':value})
    return {'social_links':social,'contact_links':contacts,'line_phone':line_phone}
