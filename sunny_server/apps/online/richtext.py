"""Small allowlisted rich text format; old plain text remains escaped."""
import re, uuid
from html import escape
from html.parser import HTMLParser
from io import BytesIO
from django import forms
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse, FileResponse, Http404
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks
from django.views.decorators.http import require_POST
from PIL import Image

MARKER='<!--sunny-rich-->'
class Cleaner(HTMLParser):
    allowed={'p','div','br','h2','h3','h4','strong','b','em','i','u','ul','ol','li','blockquote','a','img','figure','figcaption','hr'}
    def __init__(self):super().__init__(convert_charrefs=True);self.out=[]
    def handle_starttag(self,tag,attrs):
        if tag not in self.allowed:return
        attrs=dict(attrs);safe=[]
        if tag=='a':
            url=attrs.get('href','').strip()
            if url.startswith(('https://','http://','mailto:','tel:')) or (url.startswith('/') and not url.startswith('//')):safe.append(('href',url))
        if tag=='img':
            src=attrs.get('src','')
            if not re.fullmatch(r'/online/inline-images/[0-9a-f]{32}/',src):return
            safe=[('src',src),('alt',attrs.get('alt','')),('loading','lazy')]
        self.out.append('<'+tag+''.join(' '+k+'="'+escape(v,quote=True)+'"' for k,v in safe)+'>')
    def handle_endtag(self,tag):
        if tag in self.allowed and tag not in {'br','img','hr'}:self.out.append('</'+tag+'>')
    def handle_data(self,data):self.out.append(escape(data))
def sanitize(value):
    parser=Cleaner();parser.feed(value);parser.close();return ''.join(parser.out)
def render_body(value):
    value=str(value or '')
    return mark_safe(sanitize(value[len(MARKER):])) if value.startswith(MARKER) else mark_safe(linebreaks(value,autoescape=True))
class RichTextWidget(forms.Textarea):
    template_name='online/widgets/richtext.html'
    class Media:
        css={'all':('css/service_editor.css',)}
        js=('js/service_editor.js',)
    def get_context(self,name,value,attrs):
        context=super().get_context(name,value,attrs)
        context['widget']['rendered']=render_body(value)
        return context
@require_POST
def upload(request):
    if not request.user.has_perm('online.add_service') and not request.user.has_perm('online.change_service'):return JsonResponse({'error':'Không có quyền soạn dịch vụ.'},status=403)
    photo=request.FILES.get('image')
    if not photo or photo.size>5*1024*1024:return JsonResponse({'error':'Chọn ảnh JPEG, PNG hoặc WebP tối đa 5 MB.'},status=400)
    try:
        image=Image.open(photo)
        if image.format not in ('JPEG','PNG','WEBP') or image.width*image.height>25000000:raise ValueError()
        image.load();image.thumbnail((2000,2000));output=BytesIO();image.convert('RGB').save(output,'JPEG',quality=88)
    except Exception:return JsonResponse({'error':'Ảnh không hợp lệ.'},status=400)
    key=uuid.uuid4().hex
    default_storage.save('online/inline/'+key+'.jpg',ContentFile(output.getvalue()))
    return JsonResponse({'url':'/online/inline-images/'+key+'/'})
def image(request,key):
    if not re.fullmatch('[0-9a-f]{32}',key):raise Http404()
    try:response=FileResponse(default_storage.open('online/inline/'+key+'.jpg','rb'),content_type='image/jpeg')
    except FileNotFoundError:raise Http404()
    response['X-Content-Type-Options']='nosniff';return response
