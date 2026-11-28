import hashlib,json,uuid
from datetime import date,timedelta
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.db import transaction,IntegrityError,OperationalError
from django.http import JsonResponse,Http404
from django.shortcuts import get_object_or_404,redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET,require_POST,require_http_methods
from apps.legacy.models import SePayIntent,Workspace
from apps.legacy.sepay import customer_data
from .models import Service,ServiceOption,OnlineOrder,CartOrder
from .forms import CartCheckoutForm
from .language import public_render,language
from .views import quote,session_hash,checkout_ready,order_ready,owner

CART_KEY='sunny_cart_v1'
DIRECT_KEY='sunny_direct_v1'

def cart_count(request):
    return sum(int(row.get('qty',0)) for row in request.session.get(CART_KEY,{}).values())

def day_value(value):
    try:day=date.fromisoformat(value)
    except (ValueError,TypeError):raise ValueError('Chọn ngày sử dụng hợp lệ. / Choose a valid visit date.')
    if not timezone.localdate()<=day<=timezone.localdate()+timedelta(days=365):raise ValueError('Chọn ngày trong 365 ngày tới. / Choose a date within 365 days.')
    return day

def choices(service):
    rows=[]
    if service.ticket_id and not service.ticket_groups.exists():rows.append({'id':'default','title':'Vé mặc định','title_en':'Standard ticket','option':None})
    for opt in service.options.filter(active=True).select_related('group').order_by('group__sort_order','group_id','sort_order','pk'):rows.append({'id':str(opt.pk),'title':opt.display_title,'title_en':opt.display_title_en,'option':opt})
    return rows

def ticket_groups(service):
    groups={}
    audiences={'adult':('Người lớn','Adult'),'child':('Trẻ em','Child'),'senior':('Người cao tuổi','Senior')}
    for choice in choices(service):
        opt=choice['option'];group_name=((opt.group.name if opt.group_id else opt.group_name) if opt else '') or choice['title'];key=group_name.strip().casefold()
        if key not in groups:groups[key]={'title':group_name,'title_en':((opt.group.name_en if opt.group_id else opt.group_name_en) or group_name) if opt and (opt.group_id or opt.group_name) else choice['title_en'],'options':[]}
        labels=audiences.get(opt.audience) if opt else None
        groups[key]['options'].append({**choice,'title':labels[0] if labels else choice['title'],'title_en':labels[1] if labels else choice['title_en']})
    return list(groups.values())

def service_page(request,service):
    options=choices(service)
    return public_render(request,'online/service.html',{'item':service,'options':options,'ticket_groups':ticket_groups(service),'today':timezone.localdate().isoformat(),'last_day':(timezone.localdate()+timedelta(days=365)).isoformat(),'show_weather':True})

@never_cache
@require_GET
def prices(request,slug):
    service=get_object_or_404(Service,slug=slug,published=True)
    try:day=day_value(request.GET.get('date'))
    except ValueError as exc:return JsonResponse({'error':str(exc)},status=400)
    rows=[]
    for choice in choices(service):
        try:
            unit,_,_=quote(service,day,choice['option'])
            opt=choice['option']
            rows.append({'id':choice['id'],'price':unit,'available':True,'published_price':opt.published_price if opt else None,'strike_published_price':bool(opt and opt.strike_published_price and opt.published_price and unit<opt.published_price)})
        except (ValueError,KeyError,TypeError):rows.append({'id':choice['id'],'available':False})
    return JsonResponse({'date':day.isoformat(),'options':rows})

@never_cache
@require_POST
def add(request,slug):
    service=get_object_or_404(Service,slug=slug,published=True)
    error=''
    try:
        day=day_value(request.POST.get('visit_date'));direct=request.POST.get('purchase_mode')=='now';cart={} if direct else dict(request.session.get(CART_KEY,{}));added=0
        for choice in choices(service):
            raw=request.POST.get('qty_'+choice['id'],'0')
            if not raw.isdigit():raise ValueError('Số lượng không hợp lệ. / Invalid quantity.')
            qty=int(raw)
            if qty==0:continue
            if not 1<=qty<=20:raise ValueError('Mỗi loại tối đa 20 vé. / Maximum 20 tickets per option.')
            quote(service,day,choice['option'])
            key=hashlib.sha256(f'{service.pk}:{choice["id"]}:{day}'.encode()).hexdigest()[:24]
            previous=cart.get(key,{}).get('qty',0)
            if previous+qty>20:raise ValueError('Mỗi loại tối đa 20 vé. / Maximum 20 tickets per option.')
            cart[key]={'service':service.pk,'option':choice['option'].pk if choice['option'] else None,'date':day.isoformat(),'qty':previous+qty,'selected':True};added+=qty
        if not added:raise ValueError('Chọn ít nhất một vé. / Choose at least one ticket.')
        if len(cart)>20 or sum(row['qty'] for row in cart.values())>100:raise ValueError('Giỏ tối đa 20 dòng và 100 vé. / Cart limit: 20 lines and 100 tickets.')
        request.session[DIRECT_KEY if direct else CART_KEY]=cart
        return redirect('online-buy-now-checkout' if direct else 'online-cart')
    except (ValueError,KeyError,TypeError) as exc:error=str(exc)
    return public_render(request,'online/service.html',{'item':service,'options':choices(service),'ticket_groups':ticket_groups(service),'today':request.POST.get('visit_date',timezone.localdate().isoformat()),'last_day':(timezone.localdate()+timedelta(days=365)).isoformat(),'show_weather':True,'error':error})

def resolved(request,selected_only=False,direct=False):
    rows=[]
    for key,row in request.session.get(DIRECT_KEY if direct else CART_KEY,{}).items():
        if selected_only and not row.get('selected',True):continue
        result={'key':key,**row,'error':''}
        service=Service.objects.filter(pk=row['service'],published=True).first()
        option=ServiceOption.objects.filter(pk=row['option'],service=service,active=True).first() if row.get('option') else None
        result.update(service=service,option=option)
        try:
            if not service or (row.get('option') and not option):raise ValueError('Dịch vụ/loại vé ngừng bán. / Service or ticket unavailable.')
            day=day_value(row['date']);unit,ticket,cost=quote(service,day,option)
            result.update(day=day,unit=unit,total=unit*row['qty'],ticket=ticket,cost=cost)
            result['title']=(service.title_en or service.title) if language(request)=='en' else service.title
            result['option_title']=(option.display_title_en if language(request)=='en' else option.display_title) if option else ('Standard ticket' if language(request)=='en' else 'Vé mặc định')
        except (ValueError,KeyError,TypeError) as exc:result.update(error=str(exc),total=0,title=service.title if service else 'Unavailable',option_title='')
        rows.append(result)
    return rows

def digest(rows):
    return hashlib.sha256(json.dumps([{'key':r['key'],'qty':r['qty'],'unit':r.get('unit'),'date':r['date']} for r in rows],sort_keys=True).encode()).hexdigest()

@never_cache
@require_http_methods(['GET','POST'])
def page(request):
    error=''
    if request.method=='POST':
        try:
            cart=dict(request.session.get(CART_KEY,{}));updated={}
            for key,row in cart.items():
                if request.POST.get('remove')==key:continue
                qty=int(request.POST.get('qty_'+key,row['qty']))
                if not 1<=qty<=20:raise ValueError('Số lượng cần từ 1 đến 20. / Quantity must be 1 to 20.')
                updated[key]={**row,'qty':qty,'selected':key in request.POST.getlist('selected')}
            if sum(row['qty'] for row in updated.values())>100:raise ValueError('Tối đa 100 vé. / Maximum 100 tickets.')
            request.session[CART_KEY]=updated
            return redirect('online-cart')
        except (ValueError,TypeError) as exc:error=str(exc)
    rows=resolved(request)
    return public_render(request,'online/cart.html',{'rows':rows,'total':sum(r['total'] for r in rows if r.get('selected',True)),'error':error})

@never_cache
@require_http_methods(['GET','POST'])
def checkout(request,direct=False):
    key=session_hash(request)
    rows=resolved(request,True,direct)
    form=CartCheckoutForm(request.POST or None,lang=language(request),initial={'request_id':uuid.uuid4(),'quote_token':signing.dumps(digest(rows),salt='sunny-cart')})
    if request.method=='POST' and form.is_valid():
        values=form.cleaned_data
        try:
            fingerprint=hashlib.sha256(json.dumps({k:str(v) for k,v in values.items() if k not in ('request_id','website')},sort_keys=True).encode()).hexdigest()
            with transaction.atomic():
                existing=CartOrder.objects.filter(request_id=values['request_id']).first()
                if existing:
                    if existing.session_hash!=key or existing.fingerprint!=fingerprint:raise ValueError('Yêu cầu đã dùng. / Request already used.')
                    return redirect('online-cart-order',key=existing.pk)
                if not rows or any(r['error'] for r in rows):raise ValueError('Giỏ chưa có lựa chọn hợp lệ. / Choose valid cart items.')
                if signing.loads(values['quote_token'],salt='sunny-cart',max_age=1800)!=digest(rows):raise ValueError('Giá/giỏ đã thay đổi. Mở lại trang để kiểm tra. / Prices or cart changed. Reload to review.')
                if not order_ready():raise ValueError('Thanh toán tạm đóng. / Online payment is temporarily unavailable.')
                ratekey='online-cart:'+hashlib.sha256(request.META.get('REMOTE_ADDR','').encode()).hexdigest();count=cache.get(ratekey,0)
                if count>=30 or CartOrder.objects.filter(session_hash=key,created_at__gte=timezone.now()-timedelta(hours=1)).count()>=10:raise ValueError('Quá nhiều yêu cầu. / Too many requests.')
                cache.set(ratekey,count+1,3600)
                order=CartOrder.objects.create(request_id=values['request_id'],session_hash=key,fingerprint=fingerprint,customer_name=values['customer_name'],email=values['email'],phone=values['phone'],total=sum(r['total'] for r in rows),language=language(request))
                for row in rows:
                    service=row['service'];opt=row['option']
                    OnlineOrder.objects.create(cart=order,request_id=uuid.uuid4(),session_hash=key,fingerprint=fingerprint,service=service,option=opt,customer_name=order.customer_name,email=order.email,phone=order.phone,visit_date=row['day'],qty=row['qty'],unit_price=row['unit'],total=row['total'],snapshot={'title':service.title,'title_en':service.title_en,'option':opt.display_title if opt else 'Vé mặc định','option_en':opt.display_title_en if opt else 'Standard ticket','ticket':row['ticket'],'cost':row['cost']})
            cart_key=DIRECT_KEY if direct else CART_KEY
            cart=dict(request.session.get(cart_key,{}))
            for row in rows:cart.pop(row['key'],None)
            request.session[cart_key]=cart
            return redirect('online-cart-order',key=order.pk)
        except (ValueError,KeyError,TypeError,signing.BadSignature) as exc:form.add_error(None,str(exc))
        except (IntegrityError,OperationalError):form.add_error(None,'Đang xử lý, thử lại cùng yêu cầu. / Processing; retry this request.')
    return public_render(request,'online/cart_checkout.html',{'direct':direct,'form':form,'rows':rows,'total':sum(r['total'] for r in rows),'available':bool(rows) and not any(r['error'] for r in rows) and order_ready()})

def customer_order(request,key):return get_object_or_404(CartOrder,pk=key,session_hash=session_hash(request))

def state(order):
    if order.status=='paid':
        from .views import order_state
        if any(order_state(line)[0]=='review' for line in order.lines.all()):return 'review'
        if order.payment_method=='cash' and order.email_state=='external':return 'delivered'
        return 'sent' if order.email_state in ('sent','external') else 'paid'
    if order.payment_method=='cash' and order.cash_requested_at:return 'cash_pending'
    if order.intent_id:return customer_data(order.intent)['state']
    return 'pending'

def label(value,lang):
    return {'cash_pending':('Chờ liên hệ giao vé và thu tiền','Awaiting delivery arrangements & cash payment'),'delivered':('Đã giao vé và thu tiền mặt','Tickets delivered — Cash received'),'pending':('Chờ thanh toán','Awaiting payment'),'paid':('Đã thanh toán — Chờ gửi vé','Payment received — Awaiting tickets'),'sent':('Đã gửi vé qua email','Tickets sent by email')}.get(value,('Cần kiểm tra trạng thái, không thanh toán lại.','Please check the order status. Do not pay again.'))[lang=='en']

@never_cache
@require_http_methods(['GET','POST'])
def order_page(request,key):
    order=customer_order(request,key);error=''
    if request.method=='POST':
        try:
            with transaction.atomic():
                order=CartOrder.objects.select_for_update().get(pk=order.pk)
                method=request.POST.get('payment_method','bank_transfer')
                if method in ('visa','mastercard','card'):raise ValueError('Thanh toán thẻ quốc tế hiện chưa khả dụng. Vui lòng chọn QR hoặc tiền mặt. / International card payments are currently unavailable. Choose QR or cash.')
                if method not in ('bank_transfer','cash'):raise ValueError('Phương thức thanh toán không hợp lệ. / Invalid payment method.')
                if order.status!='pending':raise ValueError('Đơn không còn chờ thanh toán. / Order is no longer pending.')
                if order.payment_method=='cash':
                    if method=='cash':return redirect('online-cart-order',key=order.pk)
                    raise ValueError('Đã gửi yêu cầu giao vé. Liên hệ Sunny trước khi đổi phương thức. / Contact Sunny before changing the delivery payment method.')
                if method=='cash':
                    if not order_ready():raise ValueError('Chưa thể nhận yêu cầu. / Orders are temporarily unavailable.')
                    if order.intent_id:raise ValueError('Đơn đã tạo QR. Liên hệ Sunny để kiểm tra trước khi đổi sang tiền mặt. / A QR already exists. Contact Sunny before switching to cash.')
                    if timezone.now()>order.created_at+timedelta(minutes=30) or order.lines.filter(visit_date__lt=timezone.localdate()).exists():raise ValueError('Đơn hết hạn giữ giá, hãy đặt lại. / Price hold expired; please book again.')
                    if not request.POST.get('cash_confirmed'):raise ValueError('Xác nhận giao vé và thu tiền tại Đà Nẵng. / Confirm cash delivery in Da Nang.')
                    note=request.POST.get('delivery_note','').strip()
                    if len(note)>500:raise ValueError('Thông tin giao vé tối đa 500 ký tự. / Delivery note: maximum 500 characters.')
                    order.payment_method='cash';order.cash_requested_at=timezone.now();order.delivery_note=note
                    order.save(update_fields=['payment_method','cash_requested_at','delivery_note'])
                    from .payments import notify_admin
                    transaction.on_commit(lambda:notify_admin(order.pk))
                    return redirect('online-cart-order',key=order.pk)
                if not checkout_ready():raise ValueError('Đơn không thể tạo QR. / Payment QR unavailable.')
                if not order.intent_id:
                    if timezone.now()>order.created_at+timedelta(minutes=30) or order.lines.filter(visit_date__lt=timezone.localdate()).exists():raise ValueError('Đơn hết hạn giữ giá, hãy đặt lại. / Price hold expired; please book again.')
                    Workspace.objects.get_or_create(pk=1)
                    order.intent=SePayIntent.objects.create(owner=owner(),booking_id='CART-'+str(order.pk),booking_code=order.code,booking_version=1,booking_fingerprint=order.fingerprint,code='STP'+str(uuid.uuid4().int%10**18).zfill(18),amount=order.total,bank_code=settings.SEPAY_BANK_CODE,gateway=settings.SEPAY_GATEWAY,account_number=settings.SEPAY_ACCOUNT_NUMBER,account_name=settings.SEPAY_ACCOUNT_NAME,mode=settings.SEPAY_MODE,expires_at=timezone.now()+timedelta(seconds=settings.SEPAY_TTL_SECONDS))
                    order.payment_method='bank_transfer';order.save(update_fields=['intent','payment_method'])
        except ValueError as exc:error=str(exc)
        except (IntegrityError,OperationalError):error='Đang xử lý. / Processing, please reload.'
    current=state(order)
    response=public_render(request,'online/cart_order.html',{'order':order,'lines':order.lines.all(),'state':current,'label':label(current,language(request)),'payment':customer_data(order.intent) if order.intent_id else None,'error':error,'qr_ready':checkout_ready()})
    response['Referrer-Policy']='same-origin';return response

@never_cache
@require_GET
def status(request,key):
    order=customer_order(request,key);current=state(order)
    return JsonResponse({'state':current,'label':label(current,language(request))})
