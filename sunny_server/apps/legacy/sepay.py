"""SePay bank webhook. No browser action can declare an automatic bank payment."""
import base64
import copy
from datetime import datetime, timedelta
import hashlib
import hmac
from io import BytesIO
import json
import re
import uuid
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction, IntegrityError, OperationalError
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from .counter import permitted, payment_pending, public_booking
from .counter_details import own_booking
from .models import Workspace, SePayIntent, SePayTransaction
from .operations import save_workspace
from .pricing import amount, calculate_booking

CODE=re.compile(r'(?<![A-Z0-9])STP[0-9]{18}(?![A-Z0-9])')
SALT='sunny-sepay-customer-display-v1'

def booking_fingerprint(row):
    fields=('bookingCode','ticketId','ticketType','product','qty','sellPrice','revenue','hasVat','customerType','agent','customerName','date','customerEmail','note','counterSellerId')
    return hashlib.sha256(json.dumps({key:row.get(key) for key in fields},sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

def ready():
    return bool(settings.SEPAY_ENABLED and settings.SEPAY_MODE in ('test','live') and len(settings.SEPAY_WEBHOOK_SECRET)>=32 and re.fullmatch(r'[A-Za-z0-9_-]{2,64}',settings.SEPAY_BANK_CODE) and re.fullmatch(r'[A-Za-z0-9]{4,64}',settings.SEPAY_ACCOUNT_NUMBER) and settings.SEPAY_GATEWAY and settings.SEPAY_ACCOUNT_NAME and 60<=settings.SEPAY_TTL_SECONDS<=3600)

def active_intent(booking):
    return SePayIntent.objects.filter(booking_id=booking['id'],state='pending',expires_at__gt=timezone.now()).first()

def intent_state(intent):
    return 'expired' if intent.state=='pending' and timezone.now()>intent.expires_at else intent.state

def customer_data(intent):
    state=intent_state(intent)
    if state=='pending' and (not ready() or intent.mode!=settings.SEPAY_MODE):state='unavailable'
    result={'state':state,'code':intent.code,'bookingCode':intent.booking_code,'amount':float(intent.amount),'bank':intent.bank_code,'account':intent.account_number,'accountName':intent.account_name,'mode':intent.mode,'expiresAt':intent.expires_at.isoformat(),'qrUrl':None}
    if state=='pending':
        if intent.mode=='live':result['qrUrl']='https://vietqr.app/img?'+urlencode({'acc':intent.account_number,'bank':intent.bank_code,'amount':int(intent.amount),'des':intent.code,'template':'qronly'})
        else:
            # Deliberately not a bank QR in test mode: scanning cannot initiate real payment.
            import zxingcpp
            from PIL import Image
            pixels=zxingcpp.write_barcode_to_image(zxingcpp.create_barcode('SUNNY-SEPAY-TEST-NOT-A-PAYMENT:'+intent.code+':'+str(int(intent.amount)),zxingcpp.BarcodeFormat.QRCode),scale=5)
            height,width=memoryview(pixels).shape;image=Image.frombytes('L',(width,height),bytes(pixels));stream=BytesIO();image.save(stream,format='PNG')
            result['qrUrl']='data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()
    return result

def staff_data(intent):
    token=signing.dumps({'intent':str(intent.pk)},key=settings.SEPAY_WEBHOOK_SECRET,salt=SALT) if ready() else None
    return {'id':str(intent.pk),**customer_data(intent),'displayUrl':'/pay/sepay/#'+token if token else None}

@login_required
@never_cache
@require_POST
def create_intent(request,booking_id):
    if not permitted(request.user,'view') or not permitted(request.user,'create'):return JsonResponse({'error':'Chưa có quyền tạo QR chuyển khoản.'},status=403)
    if not ready():return JsonResponse({'error':'SePay chưa được cấu hình. Quản trị cần cấu hình ngân hàng và khóa webhook trên server.'},status=503)
    try:
        if request.body and json.loads(request.body)!={}:raise ValueError('Số tiền và tài khoản nhận phải do server xác định.')
        with transaction.atomic():
            Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);row=own_booking(data,request.user,booking_id)
            if not payment_pending(row):raise ValueError('Booking không ở trạng thái chờ thanh toán.')
            due=amount(row['revenue'])-sum(amount(p['amount']) for p in row.get('payments',[]))
            if due<=0 or due!=due.to_integral_value():raise ValueError('Số tiền chuyển khoản phải là số nguyên dương.')
            existing=active_intent(row)
            if existing:
                if existing.amount!=due or existing.booking_version!=row.get('counterVersion',1) or existing.booking_fingerprint!=booking_fingerprint(row):raise ValueError('Booking đã đổi. Hủy phiên QR cũ trước khi tạo lại.')
                return JsonResponse(staff_data(existing))
            SePayIntent.objects.filter(booking_id=booking_id,state='pending').update(state='expired')
            intent=SePayIntent.objects.create(owner=request.user,booking_id=booking_id,booking_code=row['bookingCode'],booking_version=row.get('counterVersion',1),booking_fingerprint=booking_fingerprint(row),code='STP'+str(uuid.uuid4().int%10**18).zfill(18),amount=due,bank_code=settings.SEPAY_BANK_CODE,gateway=settings.SEPAY_GATEWAY,account_number=settings.SEPAY_ACCOUNT_NUMBER,account_name=settings.SEPAY_ACCOUNT_NAME,mode=settings.SEPAY_MODE,expires_at=timezone.now()+timedelta(seconds=settings.SEPAY_TTL_SECONDS))
            row.update(paymentMethod='bank_transfer',sepayIntentId=str(intent.pk))
            save_workspace(obj,data,request.user,obj.revision,'counter.sepay_intent_create')
        return JsonResponse(staff_data(intent),status=201)
    except (RuntimeError,IntegrityError,OperationalError):return JsonResponse({'error':'Có phiên đang cập nhật. Tải lại booking trước khi tạo QR.'},status=409)
    except (ValueError,KeyError,TypeError) as exc:return JsonResponse({'error':str(exc) or 'Booking chưa hợp lệ.'},status=400)

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def staff_intent(request,intent_id):
    if not permitted(request.user,'view'):raise Http404()
    intent=get_object_or_404(SePayIntent,pk=intent_id)
    if not request.user.is_superuser and intent.owner_id!=request.user.pk:raise Http404()
    if request.method=='GET':return JsonResponse(staff_data(intent))
    if not permitted(request.user,'create'):return JsonResponse({'error':'Chưa có quyền hủy phiên chờ.'},status=403)
    try:
        body=json.loads(request.body)
        if body!={'action':'cancel'}:raise ValueError('Thao tác không hợp lệ.')
        with transaction.atomic():
            Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);row=own_booking(data,request.user,intent.booking_id)
            intent=SePayIntent.objects.select_for_update().get(pk=intent.pk)
            if intent.state=='paid':raise ValueError('Đã nhận thanh toán. Không hủy phiên đã thu tiền.')
            intent.state='cancelled';intent.save(update_fields=['state'])
            if row.get('sepayIntentId')==str(intent.pk):row['sepayIntentId']=None
            save_workspace(obj,data,request.user,obj.revision,'counter.sepay_intent_cancel')
        return JsonResponse(staff_data(intent))
    except (RuntimeError,OperationalError):return JsonResponse({'error':'Dữ liệu đã đổi; mở lại để kiểm tra.'},status=409)
    except (ValueError,TypeError):return JsonResponse({'error':'Chỉ hủy được phiên chưa nhận thanh toán.'},status=400)

@never_cache
@require_GET
def customer_page(request):
    response=render(request,'sepay_display.html');response['Referrer-Policy']='no-referrer';return response

@never_cache
@require_GET
def display_status(request):
    if not ready():return JsonResponse({'state':'unavailable','qrUrl':None},status=503)
    header=request.headers.get('Authorization','')
    if not header.startswith('Bearer '):raise Http404()
    try:
        data=signing.loads(header[7:],key=settings.SEPAY_WEBHOOK_SECRET,salt=SALT,max_age=3600,fallback_keys=[])
        intent=SePayIntent.objects.get(pk=data['intent'])
    except (signing.BadSignature,KeyError,ValueError,SePayIntent.DoesNotExist):raise Http404()
    return JsonResponse(customer_data(intent))

def bank_key(value):return re.sub(r'[^A-Z0-9]','',str(value).upper())

@csrf_exempt
@never_cache
@require_POST
def webhook(request):
    if not ready():return JsonResponse({'success':False,'error':'Unavailable'},status=503)
    try:size=int(request.META.get('CONTENT_LENGTH') or 0)
    except ValueError:return JsonResponse({'success':False},status=400)
    if size>65536:return JsonResponse({'success':False},status=413)
    raw=request.body
    stamp=request.headers.get('X-SePay-Timestamp','');signature=request.headers.get('X-SePay-Signature','')
    if len(raw)>65536 or not re.fullmatch(r'sha256=[0-9a-f]{64}',signature) or not re.fullmatch(r'\d{10,12}',stamp) or abs(timezone.now().timestamp()-int(stamp))>300:return JsonResponse({'success':False},status=401)
    expected='sha256='+hmac.new(settings.SEPAY_WEBHOOK_SECRET.encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature):return JsonResponse({'success':False},status=401)
    try:
        payload=json.loads(raw)
        if not isinstance(payload,dict):raise ValueError()
        transaction_id=str(payload['id'])
        if transaction_id=='0':return JsonResponse({'success':True,'ignored':'provider_test_message'})
        if not re.fullmatch(r'[1-9]\d{0,39}',transaction_id):raise ValueError()
        value=amount(payload['transferAmount'])
        gateway=str(payload.get('gateway',''));account=str(payload.get('accountNumber',''));content=str(payload.get('content') or '')
        reference=str(payload.get('referenceCode') or '')
        if len(gateway)>64 or len(account)>64 or len(content)>8000 or len(reference)>160:raise ValueError()
        try:transaction_at=timezone.make_aware(datetime.strptime(payload.get('transactionDate',''),'%Y-%m-%d %H:%M:%S'),ZoneInfo('Asia/Ho_Chi_Minh'))
        except (ValueError,TypeError):transaction_at=None
        with transaction.atomic():
            Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            if SePayTransaction.objects.filter(pk=transaction_id).exists():return JsonResponse({'success':True,'duplicate':True})
            event=SePayTransaction.objects.create(transaction_id=transaction_id,amount=value,gateway=gateway,account_number=account,content=content,reference_code=reference,transaction_at=transaction_at)
            codes=set(CODE.findall(content.upper()));explicit=str(payload.get('code') or '').upper()
            if CODE.fullmatch(explicit):codes.add(explicit)
            intent=SePayIntent.objects.select_for_update().filter(code=next(iter(codes))).first() if len(codes)==1 else None
            event.intent=intent;reason='Không tìm thấy duy nhất mã thanh toán.'
            if payload.get('transferType')!='in':reason='Không phải giao dịch tiền vào.';event.state='ignored'
            elif intent:
                obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data)
                row=next((b for b in data.get('bookings',[]) if b.get('id')==intent.booking_id and b.get('source')=='counter'),None)
                if intent.mode!=settings.SEPAY_MODE:reason='Môi trường thanh toán đã đổi; cần đối soát.'
                elif bank_key(gateway)!=bank_key(intent.gateway) or account!=intent.account_number:reason='Sai ngân hàng hoặc tài khoản nhận.'
                elif value!=intent.amount or value!=value.to_integral_value():reason='Số tiền thiếu/thừa hoặc không hợp lệ.'
                elif intent.state not in ('pending','expired'):reason='Phiên QR đã hủy hoặc đã thanh toán.'
                elif not transaction_at or transaction_at<intent.created_at-timedelta(seconds=60) or transaction_at>intent.expires_at:reason='Giao dịch ngoài thời gian phiên; cần đối soát.'
                elif not row or row.get('counterVersion',1)!=intent.booking_version or row.get('sepayIntentId')!=str(intent.pk) or booking_fingerprint(row)!=intent.booking_fingerprint:reason='Booking hoặc phiên QR đã thay đổi.'
                elif not payment_pending(row):reason='Booking đã ghi nhận thanh toán bằng cách khác.'
                elif amount(row['revenue'])-sum(amount(p['amount']) for p in row.get('payments',[]))!=value:reason='Công nợ booking đã đổi.'
                else:
                    before=public_booking(row);old=copy.deepcopy(row.get('payments',[]));now=timezone.now().isoformat();actor='SePay (TEST)' if intent.mode=='test' else 'SePay'
                    row.setdefault('payments',[]).append({'id':'SEPAY-'+transaction_id,'date':timezone.localtime(transaction_at).date().isoformat(),'amount':float(value),'method':'bank_transfer','provider':'sepay_test' if intent.mode=='test' else 'sepay','providerTransactionId':transaction_id,'referenceCode':reference,'note':actor+' xác nhận chuyển khoản '+intent.code,'createdAt':now,'createdBy':None})
                    row.update(status='completed',paymentMethod='bank_transfer',counterPaymentConfirmedAt=now,counterPaymentConfirmedBy=actor)
                    calculate_booking(row)
                    row.setdefault('counterHistory',[]).append({'action':'payment_confirm','at':now,'by':actor,'before':before,'after':public_booking(row),'paymentAdjustment':float(value),'paymentsBefore':old,'paymentsAfter':copy.deepcopy(row['payments'])})
                    save_workspace(obj,data,None,obj.revision,'counter.sepay_payment')
                    intent.state='paid';intent.paid_at=timezone.now();intent.save(update_fields=['state','paid_at'])
                    event.state='applied';reason='Đã ghi nhận đủ tiền cho booking.'
            event.reason=reason;event.save(update_fields=['intent','state','reason'])
        return JsonResponse({'success':True,'state':event.state})
    except (OperationalError,IntegrityError,RuntimeError):return JsonResponse({'success':False,'error':'Retry later'},status=503)
    except (ValueError,KeyError,TypeError):return JsonResponse({'success':False,'error':'Invalid payload'},status=400)
