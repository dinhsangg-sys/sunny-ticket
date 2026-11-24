import copy,hashlib,json,uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction,IntegrityError,OperationalError
from django.db.models import Q
from django.http import Http404,HttpResponseForbidden,JsonResponse,FileResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET,require_http_methods,require_POST
from apps.legacy.models import Workspace,SePayIntent,CounterTicketBatch,BookingCancellation
from apps.legacy.counter import default_cost,permitted
from apps.legacy.counter_tickets import email_ready
from apps.legacy.sepay import ready,customer_data
from apps.audit.models import AuditLog
from .models import Service,Article,OnlinePrice,OnlineOrder
from .forms import CheckoutForm
from .language import language,public_render,text

def public_root(request):
    if request.user.is_authenticated or request.get_host().split(':')[0].lower() not in settings.PUBLIC_SITE_HOSTS:
        from apps.legacy.views import home
        return home(request)
    return homepage(request)

@require_GET
def homepage(request):return public_render(request,'online/home.html',{'services':Service.objects.filter(published=True)[:6],'articles':Article.objects.filter(published=True)[:3]})

@require_GET
def services(request):return public_render(request,'online/list.html',{'services':Service.objects.filter(published=True),'articles':None,'title':'Những trải nghiệm ở Hội An','show_weather':True})

@require_GET
def articles(request):return public_render(request,'online/list.html',{'articles':Article.objects.filter(published=True),'services':None,'title':'Chuyện kể từ Hội An'})

@require_GET
def detail(request,slug,kind='service'):
    obj=get_object_or_404(Service if kind=='service' else Article,slug=slug,published=True)
    return public_render(request,'online/detail.html',{'item':obj,'kind':kind,'show_weather':kind=='service'})

@require_GET
def image(request,kind,key):
    obj=get_object_or_404(Service if kind=='service' else Article,pk=key,published=True)
    if not obj.image:raise Http404()
    response=FileResponse(obj.image.open('rb'));response['X-Content-Type-Options']='nosniff';return response

def session_hash(request):
    if not request.session.session_key:request.session.create()
    return hashlib.sha256(request.session.session_key.encode()).hexdigest()

def owner():
    return get_user_model().objects.filter(username=settings.ONLINE_PAYMENT_OWNER,is_active=True,is_superuser=True).first()

def checkout_ready():return settings.ONLINE_CHECKOUT_ENABLED and ready() and email_ready() and owner() is not None

def quote(service,day):
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    tickets=[t for t in data.get('ticketTypes',[]) if t.get('id')==service.ticket_id and t.get('active',True)]
    if len(tickets)!=1:raise ValueError('Loại vé đang tạm ngừng bán online.')
    prices=list(OnlinePrice.objects.filter(service=service,active=True,starts_on__lte=day).filter(Q(ends_on__isnull=True)|Q(ends_on__gte=day))[:2])
    if len(prices)!=1:raise ValueError('Ngày đã chọn chưa có giá online duy nhất. Vui lòng chọn ngày khác hoặc liên hệ Sunny.')
    if not 0<prices[0].price<=100000000:raise ValueError('Giá online chưa hợp lệ.')
    return prices[0].price,tickets[0],default_cost(data,service.ticket_id,day.isoformat())

@never_cache
@require_http_methods(['GET','POST'])
def checkout(request,slug):
    service=get_object_or_404(Service,slug=slug,published=True)
    form=CheckoutForm(request.POST or None,lang=language(request),initial={'request_id':uuid.uuid4(),'visit_date':timezone.localdate()})
    if request.method=='POST' and form.is_valid():
        if not checkout_ready():form.add_error(None,text('Thanh toán online đang tạm đóng. Vui lòng quay lại sau.',language(request)))
        else:
            values=form.cleaned_data;key=session_hash(request)
            fingerprint=hashlib.sha256(json.dumps({k:str(v) for k,v in values.items() if k not in ('request_id','website')},sort_keys=True).encode()).hexdigest()
            try:
                with transaction.atomic():
                    existing=OnlineOrder.objects.filter(request_id=values['request_id']).first()
                    if existing:
                        if existing.session_hash!=key or existing.service_id!=service.pk or existing.fingerprint!=fingerprint:raise ValueError('Lần đặt vé này đã dùng. Vui lòng mở lại biểu mẫu.')
                        return redirect('online-order',key=existing.pk)
                    ipkey='online-checkout:'+hashlib.sha256(request.META.get('REMOTE_ADDR','').encode()).hexdigest()
                    count=cache.get(ipkey,0)
                    if count>=30 or OnlineOrder.objects.filter(session_hash=key,created_at__gte=timezone.now()-timedelta(hours=1)).count()>=10:raise ValueError('Bạn đã gửi nhiều yêu cầu. Vui lòng thử lại sau.')
                    cache.set(ipkey,count+1,3600)
                    unit,ticket,cost=quote(service,values['visit_date'])
                    order=OnlineOrder.objects.create(request_id=values['request_id'],session_hash=key,fingerprint=fingerprint,service=service,customer_name=values['customer_name'],email=values['email'],phone=values['phone'],visit_date=values['visit_date'],qty=values['qty'],unit_price=unit,total=unit*values['qty'],snapshot={'title':service.title,'title_en':service.title_en,'ticket':ticket,'cost':cost})
                return redirect('online-order',key=order.pk)
            except (ValueError,KeyError,TypeError) as exc:form.add_error(None,text(str(exc),language(request)))
            except (IntegrityError,OperationalError):form.add_error(None,text('Yêu cầu đang được xử lý. Thử lại cùng biểu mẫu để tránh trùng đơn.',language(request)))
    return public_render(request,'online/checkout.html',{'service':service,'form':form,'available':checkout_ready()})

def customer_order(request,key):
    return get_object_or_404(OnlineOrder,pk=key,session_hash=session_hash(request))

def order_state(order):
    if order.booking_id and BookingCancellation.objects.filter(booking_id=order.booking_id).exists():return 'review','Đơn đang được hỗ trợ / đối soát'
    if order.status=='paid':
        data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
        booking=next((b for b in data.get('bookings',[]) if b.get('id')==order.booking_id),None)
        if not booking:return 'review','Booking cần được đối soát'
        if CounterTicketBatch.objects.filter(booking_id=order.booking_id,email_state='sent',customer_email__iexact=order.email,superseded_at__isnull=True,booking_version=booking.get('counterVersion',1)).exists():return 'sent','Đã gửi vé qua email'
        return 'paid','Đã thanh toán — Chờ gửi vé'
    if order.intent_id:
        state=customer_data(order.intent)['state']
        if state=='expired':return state,'QR đã hết hạn — chưa xác nhận thanh toán'
        if state in ('cancelled','unavailable'):return state,'Phiên thanh toán không khả dụng'
    return 'pending','Chờ thanh toán'

@never_cache
@require_http_methods(['GET','POST'])
def order_page(request,key):
    order=customer_order(request,key);error=''
    if request.method=='POST':
        try:
            with transaction.atomic():
                order=OnlineOrder.objects.select_for_update().get(pk=order.pk)
                if order.status!='pending':raise ValueError('Đơn đã được xử lý.')
                if not checkout_ready():raise ValueError('Thanh toán đang tạm đóng. Không chuyển tiền khi chưa có QR hợp lệ.')
                if not order.intent_id:
                    if timezone.now()>order.created_at+timedelta(minutes=30) or order.visit_date<timezone.localdate():raise ValueError('Đơn đã quá thời hạn giữ giá 30 phút. Đặt lại để kiểm tra giá mới; không chuyển tiền theo đơn cũ.')
                    Workspace.objects.get_or_create(pk=1)
                    intent=SePayIntent.objects.create(owner=owner(),booking_id='ONLINE-'+str(order.pk),booking_code=order.code,booking_version=1,booking_fingerprint=order.fingerprint,code='STP'+str(uuid.uuid4().int%10**18).zfill(18),amount=order.total,bank_code=settings.SEPAY_BANK_CODE,gateway=settings.SEPAY_GATEWAY,account_number=settings.SEPAY_ACCOUNT_NUMBER,account_name=settings.SEPAY_ACCOUNT_NAME,mode=settings.SEPAY_MODE,expires_at=timezone.now()+timedelta(seconds=settings.SEPAY_TTL_SECONDS))
                    order.intent=intent;order.save(update_fields=['intent'])
        except ValueError as exc:error=str(exc)
        except (IntegrityError,OperationalError):error='Đơn đang được cập nhật. Tải lại trang trước khi thử lại.'
    state,label=order_state(order)
    payment=customer_data(order.intent) if order.intent_id else None
    response=public_render(request,'online/order.html',{'order':order,'state':state,'label':label,'payment':payment,'error':error})
    response['Referrer-Policy']='no-referrer';return response

@never_cache
@require_GET
def status(request,key):
    order=customer_order(request,key);state,label=order_state(order)
    return JsonResponse({'state':state,'label':text(label,language(request))})

def can_process(user):return user.is_active and (user.is_superuser or user.has_perm('online.process_orders')) and permitted(user,'view') and permitted(user,'create')

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def queue(request):
    if not can_process(request.user):return HttpResponseForbidden('Cần quyền online.process_orders, counter.view và counter.create.')
    error=''
    if request.method=='POST':
        try:
            with transaction.atomic():
                Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
                order=get_object_or_404(OnlineOrder.objects.select_for_update(),pk=request.POST.get('order'),status='paid')
                if order.assigned_to_id and order.assigned_to_id!=request.user.pk:raise ValueError('Đơn đã được nhân viên khác nhận xử lý.')
                obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data)
                row=next((b for b in data.get('bookings',[]) if b.get('id')==order.booking_id),None)
                if not row:raise ValueError('Booking đã hủy hoặc không còn hoạt động. Liên hệ quản trị đối soát.')
                if not order.assigned_to_id:
                    from apps.legacy.operations import save_workspace
                    row['counterSellerId']=request.user.pk
                    save_workspace(obj,data,request.user,obj.revision,'online.claim')
                    order.assigned_to=request.user;order.save(update_fields=['assigned_to'])
                return redirect('/counter/?online='+order.booking_id)
        except (ValueError,RuntimeError) as exc:error=str(exc)
        except (OperationalError,IntegrityError):error='Có nhân viên đang cập nhật đơn. Tải lại để kiểm tra.'
    rows=[]
    orders=OnlineOrder.objects.filter(status='paid').select_related('service','assigned_to','intent')[:200]
    for order in orders:
        state,label=order_state(order);rows.append({'order':order,'state':state,'label':label,'mine':order.assigned_to_id==request.user.pk,'available':not order.assigned_to_id})
    return render(request,'online/queue.html',{'rows':rows,'error':error})
