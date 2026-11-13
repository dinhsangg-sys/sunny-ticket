"""Effective card fees are quoted and charged server-side; historical receipts keep snapshots."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, OperationalError
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from apps.audit.models import AuditLog
from .access import allowed, full_access
from .models import CardFeeRate, Workspace
from .pricing import amount

SCHEMES={'napas':'NAPAS','visa':'Visa','mastercard':'Mastercard','jcb':'JCB','unionpay':'UnionPay'}
ORIGINS={'domestic':'Trong nước','foreign':'Nước ngoài'}
SAMPLE={'domestic':[1.60,2.55,2.50,2.50,2.50],'foreign':[1.60,3.58,3.52,3.52,3.52]}

def can_manage(user):
    return user.is_active and (user.is_superuser or user.role in ('admin','operator') and (full_access(user) or allowed(user,'card_fee.manage')))

def fee_total(row):return sum((amount(p.get('cardFee',{}).get('feeAmount',0)) for p in row.get('payments',[])),Decimal(0))

def references(rate_id):
    from .models import BookingCancellation
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    found=[]
    for row in list(data.get('bookings',[]))+[r.snapshot for r in BookingCancellation.objects.all()]:
        payments=list(row.get('payments',[]))
        for history in row.get('counterHistory',[]):payments.extend(history.get('paymentsBefore',[]));payments.extend(history.get('paymentsAfter',[]))
        found.extend(p['cardFee'] for p in payments if str(p.get('cardFee',{}).get('rateId'))==str(rate_id))
    from django.apps import apps
    if apps.is_installed('apps.souvenirs'):
        Order=apps.get_model('souvenirs','SaleOrder')
        found.extend(Order.objects.filter(card_fee__rateId=str(rate_id)).values_list('card_fee',flat=True))
    return found

def rate_data(row):
    return {'id':str(row.pk),'scheme':row.scheme,'origin':row.origin,'rate':str(row.rate),'from':row.starts_on.isoformat(),'to':row.ends_on.isoformat() if row.ends_on else '', 'active':row.active,'note':row.note,'revision':row.revision,'used':bool(references(row.pk))}

def quote_fee(scheme,origin,value,day=None):
    if scheme not in SCHEMES or origin not in ORIGINS:raise ValueError('Chọn đủ loại thẻ và nơi phát hành.')
    day=day or timezone.localdate();rates=CardFeeRate.objects.filter(scheme=scheme,origin=origin,active=True,starts_on__lte=day)
    rates=rates.filter(ends_on__isnull=True)|rates.filter(ends_on__gte=day)
    found=list(rates[:2])
    if len(found)!=1:raise ValueError('Chưa có duy nhất mức phí thẻ đang hiệu lực. Liên hệ quản trị khai báo biểu phí.')
    rate=found[0];value=amount(value);fee=(value*rate.rate/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)
    return {'scheme':scheme,'origin':origin,'rateId':str(rate.pk),'rateRevision':rate.revision,'rate':str(rate.rate),'feeDate':day.isoformat(),'amount':float(value),'feeAmount':float(fee),'netAmount':float(value-fee),'includesVat':True}

def checked_values(body,old=None):
    if set(body)-{'id','revision','scheme','origin','rate','from','to','active','note'}:raise ValueError('Có trường không được hỗ trợ.')
    scheme,origin=body.get('scheme'),body.get('origin')
    if scheme not in SCHEMES or origin not in ORIGINS:raise ValueError('Loại thẻ/nơi phát hành không hợp lệ.')
    rate=amount(body.get('rate'))
    if rate>100 or rate.as_tuple().exponent < -3:raise ValueError('Phí cần từ 0–100%, tối đa 3 số thập phân.')
    start=date.fromisoformat(body['from']);end=date.fromisoformat(body['to']) if body.get('to') else None
    if end and end<start:raise ValueError('Ngày kết thúc phải từ ngày bắt đầu trở đi.')
    if type(body.get('active')) is not bool or not isinstance(body.get('note',''),str) or len(body.get('note',''))>500:raise ValueError('Trạng thái/ghi chú không hợp lệ.')
    if old:
        used=references(old.pk)
        if used and (scheme!=old.scheme or origin!=old.origin or rate!=old.rate or start!=old.starts_on):raise ValueError('Mức phí đã dùng phải giữ nguyên; hãy tạo kỳ mới.')
        if end and any(item['feeDate']>end.isoformat() for item in used):raise ValueError('Ngày kết thúc không được loại giao dịch đã tính phí.')
    if body['active']:
        others=CardFeeRate.objects.filter(scheme=scheme,origin=origin,active=True)
        if old:others=others.exclude(pk=old.pk)
        for other in others:
            if start<=(other.ends_on or date.max) and other.starts_on<=(end or date.max):raise ValueError('Kỳ phí bị trùng hiệu lực; kết thúc kỳ cũ trước khi thêm kỳ mới.')
    return {'scheme':scheme,'origin':origin,'rate':rate,'starts_on':start,'ends_on':end,'active':body['active'],'note':body.get('note','').strip()}

@login_required
@ensure_csrf_cookie
@never_cache
def management_page(request):
    if not can_manage(request.user):return HttpResponseForbidden('Chưa có quyền quản lý phí thẻ.')
    return render(request,'card_fees.html')

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def rates_api(request):
    if not can_manage(request.user):return JsonResponse({'error':'Chưa có quyền quản lý phí thẻ.'},status=403)
    if request.method=='GET':return JsonResponse({'schemes':SCHEMES,'origins':ORIGINS,'today':timezone.localdate().isoformat(),'rows':[rate_data(row) for row in CardFeeRate.objects.order_by('scheme','origin','-starts_on')]})
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict):raise ValueError('Dữ liệu không hợp lệ.')
        with transaction.atomic():
            # Serialize with settlement and other schedule changes (including SQLite).
            Workspace.objects.get_or_create(pk=1);Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            if body.get('action')=='seed':
                if set(body)!={'action','from'}:raise ValueError('Dữ liệu không hợp lệ.')
                if CardFeeRate.objects.exists():raise ValueError('Chỉ nạp mẫu khi chưa có biểu phí; tránh tạo trùng.')
                for origin,values in SAMPLE.items():
                    for scheme,rate in zip(SCHEMES,values):CardFeeRate.objects.create(**checked_values({'scheme':scheme,'origin':origin,'rate':rate,'from':body['from'],'active':True,'note':'Biểu phí người dùng cung cấp, đã gồm VAT'}))
            else:
                old=CardFeeRate.objects.get(pk=body['id']) if body.get('id') else None
                if old and (type(body.get('revision')) is not int or old.revision!=body['revision']):return JsonResponse({'error':'Biểu phí đã thay đổi. Tải lại trước khi sửa.'},status=409)
                values=checked_values(body,old)
                if old:
                    for key,value in values.items():setattr(old,key,value)
                    old.revision+=1;old.save()
                else:CardFeeRate.objects.create(**values)
            AuditLog.objects.create(user=request.user,action='card_fee.manage')
        return JsonResponse({'saved':True})
    except (OperationalError,RuntimeError):return JsonResponse({'error':'Có thao tác đang lưu. Tải lại để kiểm tra.'},status=409)
    except (ValueError,KeyError,TypeError,ValidationError,CardFeeRate.DoesNotExist) as exc:return JsonResponse({'error':str(exc) or 'Biểu phí không hợp lệ.'},status=400)

@login_required
@never_cache
@require_POST
def quote_api(request,booking_id):
    from .counter import permitted,payment_pending
    from .counter_details import own_booking
    if not permitted(request.user,'view') or not permitted(request.user,'create'):return JsonResponse({'error':'Chưa có quyền thu tiền quầy.'},status=403)
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict) or set(body)!={'scheme','origin'}:raise ValueError('Chọn loại thẻ và nơi phát hành.')
        row=own_booking(Workspace.objects.get(pk=1).data,request.user,booking_id)
        if not payment_pending(row):raise ValueError('Booking đã thanh toán; mở lại để kiểm tra.')
        due=amount(row['revenue'])-sum(amount(p['amount']) for p in row.get('payments',[]))
        return JsonResponse({'quote':quote_fee(body['scheme'],body['origin'],due)})
    except (ValueError,KeyError,TypeError) as exc:return JsonResponse({'error':str(exc)},status=400)

def protect_card_receipts(before,after):
    """Other workspace editors cannot silently alter charged card receipts."""
    from .booking_cancellation import guard_archive
    rows=after.get('bookings',[])
    if not isinstance(rows,list) or any(not isinstance(b,dict) or not isinstance(b.get('payments',[]),list) or any(not isinstance(p,dict) for p in b.get('payments',[])) for b in rows):raise ValueError('Danh sách booking/khoản thu không hợp lệ.')
    guard_archive(after)
    originals={b.get('id'):b for b in before.get('bookings',[])}
    active_ids={b.get('id') for b in rows}
    for old in originals.values():
        had_receipts=bool(old.get('payments')) or any(h.get('paymentsBefore') or h.get('paymentsAfter') for h in old.get('counterHistory',[]))
        if old.get('id') not in active_ids and had_receipts:raise ValueError('Booking từng có thanh toán: dùng Hủy booking sau đối soát để giữ lịch sử.')
    for old in originals.values():
        archived=[h for h in old.get('counterHistory',[]) if any(p.get('cardFee') for p in h.get('paymentsBefore',[])+h.get('paymentsAfter',[]))]
        new=next((b for b in after.get('bookings',[]) if b.get('id')==old.get('id')),{})
        if any(entry not in new.get('counterHistory',[]) for entry in archived):raise ValueError('Không xóa hoặc sửa lịch sử khoản thu có phí thẻ.')
    for row in after.get('bookings',[]):
        old=originals.get(row.get('id'),{});old_payments={p.get('id'):p for p in old.get('payments',[]) if p.get('cardFee')}
        new_payments={p.get('id'):p for p in row.get('payments',[])}
        if len([p for p in row.get('payments',[]) if p.get('cardFee')])!=len(old_payments) or any(new_payments.get(key)!=value for key,value in old_payments.items()) or any(p.get('cardFee') and p.get('id') not in old_payments for p in row.get('payments',[])):
            raise ValueError('Khoản thu có phí thẻ phải điều chỉnh tại quầy; không sửa/xóa trực tiếp lịch sử thu.')
        if old_payments and amount(row.get('revenue',0))!=amount(old.get('revenue',0)):raise ValueError('Booking có phí thẻ đã thu: cần đối soát trước khi đổi tổng tiền.')
    existing_ids={row.get('id') for row in after.get('bookings',[])}
    if any(any(p.get('cardFee') for p in row.get('payments',[])) and row.get('id') not in existing_ids for row in before.get('bookings',[])):raise ValueError('Không xóa booking đã có phí thẻ; cần đối soát khoản thu trước.')
