"""Local FAQ assistant. No external requests, AI APIs, booking or payment access."""
import json,re,unicodedata
from difflib import SequenceMatcher
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse,Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.crypto import salted_hmac
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET,require_POST
from .models import Service,ServiceFAQ
from .language import language
from .contacts import public_contacts


def context(request):
    return {'sunny_chat_enabled':getattr(settings,'SUNNY_CHAT_ENABLED',True) and not request.path.startswith(('/online/staff/','/admin/'))}

def normalized(value):
    value=unicodedata.normalize('NFKD',value.lower().replace('đ','d'))
    value=''.join(c for c in value if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+',value))

def contains(text,phrase):return ' '+phrase+' ' in ' '+text+' '

def handoff_links():
    return [row for row in public_contacts()['contact_links'] if row['label'] in ('WhatsApp','Zalo')]

def response_data(request,service=None,answer='',handoff=False,suggestions=None):
    english=language(request)=='en'
    return {'answer':answer,'handoff':handoff,'contacts':handoff_links(),'suggestions':suggestions or [],'service_url':('/services/'+service.slug+'/') if service else '', 'service_link_label':'View service & tickets' if english else 'Xem dịch vụ & chọn vé'}

def fallback(request,service,**extra):
    answer='I do not have a verified answer to this question yet. Please choose WhatsApp or Zalo below to ask our team directly.' if language(request)=='en' else 'Mình chưa có câu trả lời đã được Sunny xác nhận cho câu hỏi này. Bạn chọn WhatsApp hoặc Zalo bên dưới để nhân viên tư vấn trực tiếp nhé.'
    return response_data(request,service,answer,True,**extra)

def available():
    if not getattr(settings,'SUNNY_CHAT_ENABLED',True):raise Http404()

@never_cache
@ensure_csrf_cookie
@require_GET
def services(request):
    available();english=language(request)=='en'
    rows=[{'id':service.pk,'title':service.title_en or service.title if english else service.title,'slug':service.slug} for service in Service.objects.filter(published=True)[:200]]
    return JsonResponse({'services':rows,'csrf_token':get_token(request),'contacts':handoff_links(),'mode':'local_faq'})

def rate_allowed(request):
    # Hash only the direct peer address; do not trust client-supplied forwarding headers.
    value=salted_hmac('sunny-chat-rate',request.META.get('REMOTE_ADDR','unknown')).hexdigest()
    key='sunny-chat-minute:'+value
    if cache.add(key,1,60):return True
    try:return cache.incr(key)<=20
    except ValueError:return False

@never_cache
@require_POST
def ask(request):
    available()
    if not rate_allowed(request):
        data=fallback(request,None);data['answer']='Please wait a minute or contact our team below.' if language(request)=='en' else 'Bạn đợi một phút rồi thử lại, hoặc chọn nhân viên tư vấn bên dưới nhé.'
        return JsonResponse(data,status=429)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0)>8192:raise ValueError()
        if len(request.body)>8192:raise ValueError()
        payload=json.loads(request.body)
        if not isinstance(payload,dict) or set(payload)-{'service','message','lang'}:raise ValueError()
        if not isinstance(payload.get('service'),int) or isinstance(payload['service'],bool):raise ValueError()
        message=payload.get('message')
        if not isinstance(message,str) or not 2<=len(message.strip())<=600:raise ValueError()
    except (ValueError,TypeError,UnicodeError):return JsonResponse({'error':'Câu hỏi không hợp lệ. / Invalid question.'},status=400)
    service=get_object_or_404(Service,pk=payload['service'],published=True)
    text=normalized(message);english=language(request)=='en'
    # Personal transaction questions always go to a person. No order state is read here.
    if any(contains(text,p) for p in ('nhan vien','tu van truc tiep','nguoi that','human','staff','agent','hoan tien','refund','ma booking','ma don','otp','the tin dung','credit card','payment failed','thanh toan loi','chua nhan ve','order status','doi soat')) or re.search(r'\b(?:ON|SC|ST)-[A-Z0-9-]+',message,re.I) or re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}',message,re.I):
        return JsonResponse(fallback(request,service))
    # Dynamic prices are checked on the live booking form, not copied into FAQ answers.
    if any(contains(text,p) for p in ('gia ve','bao nhieu tien','gia bao nhieu','ticket price','price','pricing','cost','gia','discount','khuyen mai')):
        answer='Please open “View service & tickets” below and choose your visit date and ticket type to see the current online price. I cannot confirm a final price without those selections.' if english else 'Bạn mở “Xem dịch vụ & chọn vé” bên dưới, chọn ngày sử dụng và loại vé để xem giá online đang áp dụng nhé. Mình chưa xác nhận giá cuối cùng khi chưa có các lựa chọn này.'
        return JsonResponse(response_data(request,service,answer))
    faqs=list(ServiceFAQ.objects.filter(service=service,active=True)[:200])
    matches=[];exact_matches=[]
    for faq in faqs:
        if english and not faq.answer_en:continue
        phrases=[normalized(p) for p in faq.keywords.split(',') if len(normalized(p))>=3]
        questions=[normalized(faq.question),normalized(faq.question_en)]
        exact=text in questions
        if exact:exact_matches.append(faq)
        hit=exact or any(contains(text,p) for p in phrases)
        if hit:matches.append(faq)
    if exact_matches:matches=exact_matches
    if not matches:
        # Conservative typo tolerance for an almost identical approved question.
        scored=[]
        for faq in faqs:
            if english and not faq.answer_en:continue
            score=max((SequenceMatcher(None,text,normalized(q)).ratio() for q in (faq.question,faq.question_en) if len(normalized(q))>=12),default=0)
            if score>=.88:scored.append((score,faq))
        scored.sort(key=lambda item:item[0],reverse=True)
        if scored and (len(scored)==1 or scored[0][0]-scored[1][0]>=.1):matches=[scored[0][1]]
    if len(matches)==1:
        faq=matches[0]
        return JsonResponse(response_data(request,service,faq.answer_en if english else faq.answer))
    suggestions=[{'question':(f.question_en or f.question) if english else f.question} for f in (matches or faqs) if (not english or f.answer_en)][:4]
    return JsonResponse(fallback(request,service,suggestions=suggestions))
