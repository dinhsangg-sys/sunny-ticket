"""Separate counter workflow: allow-list requests and responses; costs stay server-side."""
import copy
import hashlib
import json
import uuid
from django.contrib.auth.decorators import login_required
from django.db import transaction, OperationalError
from django.http import JsonResponse, HttpResponseForbidden
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .access import allowed
from .models import Workspace
from .operations import save_workspace
from .pricing import amount, calculate_booking, supplier_options
from .ticket_lifecycle import enforce_ticket_lifecycle

PAYMENT_METHODS={'cash':'Tiền mặt','card':'Thẻ thanh toán','bank_transfer':'Chuyển khoản'}

def payment_pending(row):
    return row.get('counterPaymentFlow')=='manual_confirmation_v1' and (not row.get('counterPaymentConfirmedAt') or sum(amount(p['amount']) for p in row.get('payments',[]))<amount(row.get('revenue',0)))

def permitted(user,action):
    return user.is_active and (user.is_superuser or user.role in ('counter','admin','operator') and allowed(user,'counter.'+action))

def default_cost(data,ticket_id,day):
    rows=[p for p in supplier_options(data,ticket_id,day) if p.get('isDefault')]
    if not rows: raise ValueError('Loại vé chưa có giá vốn mặc định hợp lệ. Liên hệ quản trị.')
    # Match the existing priority for date-effective defaults, but never break a tie arbitrarily.
    latest=max(p.get('from') or '' for p in rows)
    top=[p for p in rows if (p.get('from') or '')==latest]
    if len(top)!=1: raise ValueError('Loại vé có nhiều giá vốn mặc định cùng ưu tiên. Liên hệ quản trị xác định lại.')
    return top[0]

def public_booking(row):
    fields=('id','bookingCode','date','ticketId','ticketType','product','qty','sellPrice','revenue','hasVat','note','agent','createdAt','customerEmail','counterVersion','sepayIntentId')
    result={key:row.get(key) for key in fields}
    paid=sum(amount(p['amount']) for p in row.get('payments',[]))
    result.update(paid=float(paid),balance=float(amount(row.get('revenue',0))-paid),paymentRevision=row.get('counterPaymentRevision',0))
    result.update(paymentMethod=row.get('paymentMethod',''),paymentPending=payment_pending(row),paymentStatus='pending_payment' if payment_pending(row) else 'completed' if paid>=amount(row.get('revenue',0)) else 'unpaid',paymentConfirmedAt=row.get('counterPaymentConfirmedAt'),paymentConfirmedBy=row.get('counterPaymentConfirmedBy'))
    return result

@login_required
@never_cache
@ensure_csrf_cookie
def counter_page(request):
    if not permitted(request.user,'view'): return HttpResponseForbidden('Chưa được cấp quyền vào quầy bán vé.')
    return render(request,'counter.html')

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def counter_api(request):
    user=request.user
    if not permitted(user,'view') or request.method=='POST' and not permitted(user,'create'):
        return JsonResponse({'error':'Chưa được cấp quyền thao tác tại quầy.'},status=403)
    obj,_=Workspace.objects.get_or_create(pk=1)
    day=timezone.localdate().isoformat()
    if request.method=='GET':
        tickets=[]
        for ticket in obj.data.get('ticketTypes',[]):
            if not ticket.get('active',True):continue
            try:default_cost(obj.data,ticket['id'],day);ready=True
            except (ValueError,KeyError,TypeError):ready=False
            tickets.append({'id':ticket['id'],'name':ticket.get('name',''),'product':ticket.get('product',''),'ready':ready})
        own=[public_booking(b) for b in obj.data.get('bookings',[]) if b.get('source')=='counter' and b.get('counterSellerId')==user.pk]
        own.sort(key=lambda b:b.get('createdAt') or '',reverse=True)
        from .sepay import ready
        return JsonResponse({'sepayEnabled':ready(),'today':day,'seller':user.get_username(),'canCreate':permitted(user,'create'),'canConfirmPayment':permitted(user,'create'),'canChange':permitted(user,'change'),'canReplace':permitted(user,'replace_tickets'),'canReport':permitted(user,'report'),'tickets':tickets,'bookings':own[:100]})
    try:
        body=json.loads(request.body)
        fields={'requestId','ticketId','qty','sellPrice','hasVat','note','customerEmail','paymentMethod'}
        if not isinstance(body,dict) or set(body)-fields: raise ValueError('Không được thay ngày, người bán, giá vốn hoặc các trường ngoài biểu mẫu quầy.')
        email=body.get('customerEmail','').strip()
        if email:validate_email(email)
        if len(email)>254:raise ValueError('Email quá dài.')
        request_id=str(uuid.UUID(body['requestId']))
        method=body.get('paymentMethod','cash')
        if method not in PAYMENT_METHODS:raise ValueError('Phương thức thanh toán không hợp lệ.')
        ticket_id=body['ticketId'];qty=amount(body['qty']);price=amount(body['sellPrice']);vat=body.get('hasVat',False);note=body.get('note','')
        if qty<=0 or qty!=qty.to_integral_value() or qty>10000: raise ValueError('Số lượng phải là số nguyên từ 1 đến 10000.')
        if price!=price.to_integral_value(): raise ValueError('Giá bán nhập theo đồng, không có phần thập phân.')
        amount(price*qty)
        if not isinstance(vat,bool) or not isinstance(note,str) or len(note)>2000 or not isinstance(ticket_id,str):raise ValueError('VAT/ghi chú/loại vé không hợp lệ.')
        fingerprint=hashlib.sha256(json.dumps({'ticketId':ticket_id,'qty':str(qty.normalize()),'price':str(price.normalize()),'vat':vat,'note':note,'email':email,'paymentMethod':method},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        data=copy.deepcopy(obj.data)
        existing=next((b for b in data.get('bookings',[]) if b.get('counterRequestId')==request_id and b.get('counterSellerId')==user.pk),None)
        if existing:
            if existing.get('counterRequestHash')!=fingerprint:raise ValueError('Mã lần lưu đã dùng cho nội dung khác. Kiểm tra booking vừa tạo trước khi mở giao dịch mới.')
            return JsonResponse({'booking':public_booking(existing),'duplicate':True})
        tickets=[t for t in data.get('ticketTypes',[]) if t.get('id')==ticket_id and t.get('active',True)]
        if len(tickets)!=1:raise ValueError('Loại vé không còn hoạt động hoặc không hợp lệ.')
        ticket=tickets[0];cost=default_cost(data,ticket_id,day)
        prefix='ST-'+day.replace('-','')+'-'
        numbers=[int(str(b.get('bookingCode'))[len(prefix):]) for b in data.get('bookings',[]) if str(b.get('bookingCode','')).startswith(prefix) and str(b.get('bookingCode'))[len(prefix):].isdigit()]
        row={'id':'COUNTER-'+str(uuid.uuid4()),'bookingCode':prefix+str(max(numbers,default=0)+1).zfill(3),'date':day,'createdAt':timezone.now().isoformat(),
             'source':'counter','counterSellerId':user.pk,'counterRequestId':request_id,'counterRequestHash':fingerprint,
             'customerType':'retail','agent':user.get_username(),'customerName':user.get_username(),'ticketId':ticket_id,'ticketType':ticket.get('name',''),'product':ticket.get('product',''),
             'qty':int(qty),'sellPrice':float(price),'buyPrice':float(amount(cost['price'])),'cost':0,'costSource':'supplier','costPriceId':cost['id'],'supplierId':cost['supplierId'],'supplierName':cost['supplierName'],
             'customerEmail':email,'hasVat':vat,'vatRate':15 if vat else 0,'note':note,'status':'pending_payment','paymentMethod':method,'counterPaymentFlow':'manual_confirmation_v1','payments':[],'supplierPayments':[]}
        calculate_booking(row)
        row['counterVersion']=1
        data.setdefault('bookings',[]).append(row);enforce_ticket_lifecycle(obj.data,data)
        with transaction.atomic():save_workspace(obj,data,user,obj.revision,'counter.booking_create')
        return JsonResponse({'booking':public_booking(row),'duplicate':False},status=201)
    except (RuntimeError,OperationalError):return JsonResponse({'error':'Có giao dịch khác đang lưu. Hãy thử lại cùng lần lưu; hệ thống sẽ kiểm tra để tránh tạo trùng.'},status=409)
    except (ValueError,TypeError,KeyError,AttributeError,ValidationError):return JsonResponse({'error':'Dữ liệu chưa hợp lệ hoặc giá vốn mặc định chưa sẵn sàng. Kiểm tra số lượng/giá bán và liên hệ quản trị nếu loại vé chưa có mặc định rõ ràng.'},status=400)
