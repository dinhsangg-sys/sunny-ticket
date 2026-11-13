"""Archive a reconciled booking atomically; never erase payment or QR evidence."""
import copy,hashlib,json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction,OperationalError,IntegrityError
from django.http import JsonResponse,Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods,require_GET
from .models import Workspace,BookingCancellation,SePayIntent
from .access import allowed,full_access
from .pricing import amount
from .counter import public_booking

def can_cancel(user):return user.is_authenticated and user.is_active and (user.is_superuser or user.role=='admin' or allowed(user,'booking.cancel_paid'))
def all_bookings(user):return user.is_superuser or user.role in ('admin','operator')
def can_reconcile_supplier(user):return user.is_superuser or user.role=='admin' or user.role=='operator' and (full_access(user) or allowed(user,'supplier_payment.view'))
def scoped(row,user):return all_bookings(user) or row.get('source')=='counter' and row.get('counterSellerId')==user.pk
def token(row):return hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
def fee_recorded(row):
    groups=[row.get('payments',[])]
    for h in row.get('counterHistory',[]):groups.extend([h.get('paymentsBefore',[]),h.get('paymentsAfter',[])])
    return max([sum((amount(p.get('cardFee',{}).get('feeAmount',0)) for p in group),Decimal(0)) for group in groups] or [Decimal(0)])
def summary(record):
    return {'id':record.pk,'booking':public_booking(record.snapshot),'reason':record.reason,'resolution':record.resolution,'reference':record.reference,'retainedFee':float(record.retained_fee),'cancelledAt':record.cancelled_at.isoformat(),'cancelledBy':record.cancelled_by.get_username() if record.cancelled_by else 'Tài khoản đã xóa'}
def guard_archive(data):
    records=list(BookingCancellation.objects.values('booking_id','booking_code'))
    ids={r['booking_id'] for r in records};codes={r['booking_code'] for r in records if r['booking_code']}
    if any(b.get('id') in ids or b.get('bookingCode') in codes for b in data.get('bookings',[])):raise ValueError('Không khôi phục hoặc tái dùng mã booking đã hủy; tạo booking mới nếu cần.')
    entries=data.get('cancelledBookingCodes',[])
    if not isinstance(entries,list) or any(not isinstance(b,dict) for b in entries):raise ValueError('Danh sách mã booking đã hủy không hợp lệ.')
    reserved={(b.get('id'),b.get('bookingCode')) for b in entries}
    if not {(r['booking_id'],r['booking_code']) for r in records}.issubset(reserved):raise ValueError('Cần giữ danh sách mã booking đã hủy. Tải lại dữ liệu máy chủ.')

@login_required
@never_cache
@require_GET
def cancellations(request):
    if not can_cancel(request.user):return JsonResponse({'error':'Chưa có quyền hủy booking có thanh toán.'},status=403)
    rows=BookingCancellation.objects.select_related('cancelled_by').order_by('-cancelled_at')
    if not all_bookings(request.user):rows=rows.filter(snapshot__counterSellerId=request.user.pk)
    return JsonResponse({'canCancel':True,'rows':[summary(r) for r in rows[:200]]})

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def cancel_booking(request,booking_id):
    if not can_cancel(request.user):return JsonResponse({'error':'Chưa có quyền hủy booking có thanh toán.'},status=403)
    try:
        with transaction.atomic():
            Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            obj=get_object_or_404(Workspace,pk=1);data=copy.deepcopy(obj.data)
            archived=BookingCancellation.objects.filter(booking_id=booking_id).select_related('cancelled_by').first()
            if archived:
                if not scoped(archived.snapshot,request.user):raise Http404()
                return JsonResponse({'cancelled':True,'duplicate':True,'record':summary(archived)})
            row=next((b for b in data.get('bookings',[]) if b.get('id')==booking_id and scoped(b,request.user)),None)
            if row is None:raise Http404()
            fee=fee_recorded(row)
            supplier_paid=sum((amount(p['amount']) for p in row.get('supplierPayments',[])),Decimal(0))
            if request.method=='GET':return JsonResponse({'booking':public_booking(row),'token':token(row),'recordedFee':float(fee),'hasSupplierPayments':supplier_paid>0,'supplierPaid':float(supplier_paid) if can_reconcile_supplier(request.user) else None})
            if supplier_paid>0 and not can_reconcile_supplier(request.user):raise ValueError('Booking đã chi tiền nhà cung cấp. Cần quản trị đối soát và hủy.')
            body=json.loads(request.body)
            if not isinstance(body,dict) or set(body)!={'token','reason','resolution','reference','retainedFee','confirmed'} or body['confirmed'] is not True:raise ValueError('Cần xác nhận đã đối soát tiền, phí và vé trước khi hủy.')
            if body['token']!=token(row):return JsonResponse({'error':'Booking đã thay đổi. Mở lại để đối soát số tiền mới.'},status=409)
            reason=body['reason'];reference=body['reference'];resolution=body['resolution']
            if not isinstance(reason,str) or not 5<=len(reason.strip())<=500 or not isinstance(reference,str) or len(reference)>200:raise ValueError('Lý do cần 5–500 ký tự; tham chiếu tối đa 200 ký tự.')
            if resolution not in ('mistake','refunded'):raise ValueError('Chọn tình trạng đối soát thực tế.')
            if resolution=='refunded' and len(reference.strip())<5:raise ValueError('Nhập tham chiếu hoàn/hủy tiền từ 5 ký tự.')
            if resolution=='mistake' and any(p.get('provider')=='sepay' for p in row.get('payments',[])):raise ValueError('SePay đã ghi nhận tiền thật; cần xác nhận hoàn/hủy tiền và nhập tham chiếu.')
            retained=amount(body['retainedFee'])
            if retained!=retained.to_integral_value() or retained>fee:raise ValueError('Phí không được hoàn phải là số đồng nguyên, không vượt phí đã ghi nhận.')
            record=BookingCancellation.objects.create(booking_id=booking_id,booking_code=row.get('bookingCode') or booking_id,snapshot=copy.deepcopy(row),reason=reason.strip(),reference=reference.strip(),resolution=resolution,retained_fee=retained,cancelled_by=request.user)
            data['bookings']=[b for b in data.get('bookings',[]) if b.get('id')!=booking_id]
            data.setdefault('cancelledBookingCodes',[]).append({'id':booking_id,'bookingCode':record.booking_code,'date':row.get('date',''),'counterRequestId':row.get('counterRequestId'),'counterSellerId':row.get('counterSellerId')})
            if retained:data.setdefault('cashTransactions',[]).append({'id':'CANCEL-FEE-'+str(record.pk),'date':timezone.localdate().isoformat(),'kind':'expense','category':'Phí thẻ không hoàn khi hủy booking','amount':float(retained),'note':record.booking_code+' · '+reason.strip()})
            SePayIntent.objects.filter(booking_id=booking_id,state__in=['pending','expired']).update(state='cancelled')
            from .operations import save_workspace
            save_workspace(obj,data,request.user,obj.revision,'booking.cancel_paid')
        return JsonResponse({'cancelled':True,'record':summary(record)})
    except (RuntimeError,OperationalError,IntegrityError):return JsonResponse({'error':'Có thao tác khác đang lưu. Tải lại trước khi hủy.'},status=409)
    except (ValueError,TypeError,KeyError,AttributeError) as exc:return JsonResponse({'error':str(exc) or 'Dữ liệu đối soát chưa hợp lệ.'},status=400)
