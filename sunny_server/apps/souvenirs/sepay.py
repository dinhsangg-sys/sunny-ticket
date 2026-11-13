"""Souvenir orders share authenticated SePay webhook and customer display, not ticket revenue."""
import hashlib,json,uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction,OperationalError,IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from apps.legacy.models import Workspace,SePayIntent
from apps.legacy.sepay import ready,staff_data,bank_key
from apps.audit.models import AuditLog
from .models import SaleOrder

def order_key(order):return 'SOUVENIR-'+str(order.pk)
def fingerprint(order):return hashlib.sha256((str(order.pk)+':'+str(order.revision)+':'+str(order.total)).encode()).hexdigest()
def invalidate(order):SePayIntent.objects.filter(booking_id=order_key(order),state='pending').update(state='cancelled')

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def intent_api(request,key):
    from .views import enabled,can,own_order
    enabled()
    if not can(request.user,'sell'):return JsonResponse({'error':'Chưa có quyền tạo QR Souvenirs.'},status=403)
    try:
        with transaction.atomic():
            Workspace.objects.get_or_create(pk=1);Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            order=own_order(request,key)
            if request.method=='GET':
                current=SePayIntent.objects.filter(booking_id=order_key(order)).order_by('-created_at').first()
                return JsonResponse({'status':order.status,'deleted':bool(order.deleted_at),'intent':staff_data(current) if current else None})
            body=json.loads(request.body or '{}')
            if body=={'action':'cancel'}:
                invalidate(order);return JsonResponse({'cancelled':True})
            if not isinstance(body,dict) or set(body)-{'revision'}:raise ValueError('Số tiền và tài khoản nhận phải do máy chủ xác định.')
            if not ready():return JsonResponse({'error':'SePay chưa được cấu hình hoặc chưa bật trên máy chủ.'},status=503)
            if body.get('revision',0)!=order.revision or type(body.get('revision',0)) is not int:return JsonResponse({'error':'Đơn đã thay đổi. Đóng và tải lại trước khi tạo QR.'},status=409)
            if order.deleted_at or order.status!='pending' or order.total<=0:raise ValueError('Chỉ tạo QR cho đơn chờ thanh toán có tổng tiền lớn hơn 0.')
            old=SePayIntent.objects.filter(booking_id=order_key(order),state='pending').first()
            if old and old.expires_at>timezone.now() and old.booking_version==order.revision and old.booking_fingerprint==fingerprint(order) and old.mode==settings.SEPAY_MODE:return JsonResponse(staff_data(old))
            invalidate(order)
            current=SePayIntent.objects.create(owner=request.user,booking_id=order_key(order),booking_code=order.code,booking_version=order.revision,booking_fingerprint=fingerprint(order),code='STP'+str(uuid.uuid4().int%10**18).zfill(18),amount=order.total,bank_code=settings.SEPAY_BANK_CODE,gateway=settings.SEPAY_GATEWAY,account_number=settings.SEPAY_ACCOUNT_NUMBER,account_name=settings.SEPAY_ACCOUNT_NAME,mode=settings.SEPAY_MODE,expires_at=timezone.now()+timedelta(seconds=settings.SEPAY_TTL_SECONDS))
            AuditLog.objects.create(user=request.user,action='souvenirs.sepay_create:'+str(order.pk))
            return JsonResponse(staff_data(current),status=201)
    except (ValueError,TypeError):return JsonResponse({'error':'Yêu cầu QR chưa hợp lệ hoặc đơn không còn chờ thanh toán.'},status=400)
    except (OperationalError,IntegrityError):return JsonResponse({'error':'Dữ liệu đang cập nhật. Tải lại trước khi tạo QR.'},status=409)

def apply_event(event,intent):
    from .views import order_data
    if not settings.SOUVENIRS_ENABLED:return 'Module Souvenirs đang tắt; cần đối soát.'
    order=SaleOrder.objects.filter(pk=intent.booking_id[len('SOUVENIR-'):]).prefetch_related('lines').first()
    if intent.mode!=settings.SEPAY_MODE:return 'Môi trường thanh toán đã đổi.'
    if bank_key(event.gateway)!=bank_key(intent.gateway) or event.account_number!=intent.account_number:return 'Sai ngân hàng hoặc tài khoản nhận.'
    if event.amount!=intent.amount or event.amount!=event.amount.to_integral_value():return 'Số tiền thiếu/thừa hoặc không hợp lệ.'
    if intent.state not in ('pending','expired'):return 'Phiên QR đã hủy hoặc đã thanh toán.'
    if not event.transaction_at or event.transaction_at<intent.created_at-timedelta(seconds=60) or event.transaction_at>intent.expires_at:return 'Giao dịch ngoài thời gian phiên; cần đối soát.'
    if not order or order.deleted_at or order.status!='pending' or order.revision!=intent.booking_version or fingerprint(order)!=intent.booking_fingerprint or order.total!=event.amount:return 'Đơn hoặc QR đã thay đổi; cần đối soát.'
    before=order_data(order);before.pop('history',None)
    order.status='paid';order.payment_method='bank_transfer';order.card_fee={};order.paid_at=event.transaction_at;order.paid_by=None;order.revision+=1
    after=order_data(order);after.pop('history',None)
    order.history.append({'action':'sepay','at':timezone.now().isoformat(),'actor':'SePay (TEST)' if intent.mode=='test' else 'SePay','reason':'Giao dịch '+event.pk+' · '+intent.code,'before':before,'after':after})
    order.save();intent.state='paid';intent.paid_at=timezone.now();intent.save(update_fields=['state','paid_at']);event.state='applied'
    AuditLog.objects.create(action='souvenirs.sepay_paid:'+str(order.pk))
    return 'Đã ghi nhận đủ tiền cho đơn Souvenirs.'
