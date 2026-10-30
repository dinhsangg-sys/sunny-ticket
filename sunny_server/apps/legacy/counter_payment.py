"""Explicit staff acknowledgment of actual payment; this does not contact a bank."""
import copy
import json
import uuid
from django.contrib.auth.decorators import login_required
from django.db import transaction, OperationalError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from .counter import permitted, public_booking, PAYMENT_METHODS, payment_pending
from .counter_details import own_booking
from .models import Workspace
from .operations import save_workspace
from .pricing import amount, calculate_booking

@login_required
@never_cache
@require_POST
def confirm_payment(request,booking_id):
    user=request.user
    if not permitted(user,'view') or not permitted(user,'create'):return JsonResponse({'error':'Không có quyền xác nhận thanh toán quầy.'},status=403)
    obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);row=own_booking(data,user,booking_id)
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict) or set(body)-{'version','paymentMethod','confirmed','paymentRevision'} or body.get('confirmed') is not True:raise ValueError('Cần xác nhận đã nhận tiền thực tế.')
        revision=body.get('paymentRevision',0)
        if type(revision) is not int or revision!=row.get('counterPaymentRevision',0):return JsonResponse({'error':'Trạng thái thu tiền đã đổi. Mở lại booking trước khi xác nhận.'},status=409)
        method=body.get('paymentMethod',row.get('paymentMethod','cash'))
        if not isinstance(method,str) or method not in PAYMENT_METHODS:raise ValueError('Phương thức thanh toán không hợp lệ.')
        if row.get('counterPaymentFlow')!='manual_confirmation_v1':raise ValueError('Booking cũ giữ cách ghi nhận thanh toán hiện có; quản trị đối soát nếu cần.')
        if row.get('sepayIntentId'):
            from .sepay import active_intent
            if active_intent(row):raise ValueError('Đang chờ SePay xác nhận. Nếu đổi cách thu, hủy phiên QR trước; QR ngân hàng cũ không tự vô hiệu.')
        paid=sum(amount(p['amount']) for p in row.get('payments',[]));total=amount(row['revenue'])
        if row.get('counterPaymentConfirmedAt') and paid>=total:
            if row.get('paymentMethod')!=method:raise ValueError('Booking đã xác nhận bằng phương thức khác. Không thay lịch sử thu tiền.')
            return JsonResponse({'booking':public_booking(row),'duplicate':True})
        if type(body.get('version')) is not int or body['version']!=row.get('counterVersion',1):return JsonResponse({'error':'Booking vừa thay đổi. Mở lại để kiểm tra số tiền trước khi xác nhận.'},status=409)
        if paid>total:raise ValueError('Khoản thu vượt tổng tiền; cần quản trị đối soát.')
        before=public_booking(row);old_payments=copy.deepcopy(row.get('payments',[]));delta=total-paid;now=timezone.now().isoformat()
        if delta>0:row.setdefault('payments',[]).append({'id':str(uuid.uuid4()),'date':timezone.localdate().isoformat(),'amount':float(delta),'method':method,'note':'Xác nhận đã thu tại quầy — '+PAYMENT_METHODS[method]+' — '+user.get_username(),'createdBy':user.pk,'createdAt':now})
        row.update(status='completed',paymentMethod=method,counterPaymentConfirmedAt=now,counterPaymentConfirmedBy=user.get_username())
        calculate_booking(row)
        row.setdefault('counterHistory',[]).append({'action':'payment_confirm','at':now,'by':user.get_username(),'before':before,'after':public_booking(row),'paymentAdjustment':float(delta),'paymentsBefore':old_payments,'paymentsAfter':copy.deepcopy(row.get('payments',[]))})
        # Payment acknowledgment does not change ticket content/version; imported drafts stay valid.
        with transaction.atomic():save_workspace(obj,data,user,obj.revision,'counter.payment_confirm')
        return JsonResponse({'booking':public_booking(row),'duplicate':False})
    except (RuntimeError,OperationalError):return JsonResponse({'error':'Có giao dịch khác đang lưu. Mở lại booking để kiểm tra; không xác nhận trùng.'},status=409)
    except (ValueError,TypeError,KeyError,AttributeError) as exc:return JsonResponse({'error':str(exc) or 'Dữ liệu thanh toán không hợp lệ.'},status=400)


@login_required
@never_cache
@require_POST
def reopen_payment(request,booking_id):
    user=request.user
    if not permitted(user,'view') or not permitted(user,'reopen_payment'):
        return JsonResponse({'error':'Chưa có quyền hủy xác nhận thanh toán nhầm.'},status=403)
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict) or set(body)!={'version','paymentRevision','paymentMethod','reason','confirmed'} or body['confirmed'] is not True:raise ValueError('Cần xác nhận sửa khoản thu đã ghi nhầm.')
        method=body['paymentMethod'];reason=body['reason']
        if not isinstance(method,str) or method not in PAYMENT_METHODS:raise ValueError('Phương thức thanh toán không hợp lệ.')
        if not isinstance(reason,str) or not 5<=len(reason.strip())<=500:raise ValueError('Nhập lý do sửa từ 5 đến 500 ký tự.')
        with transaction.atomic():
            Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);row=own_booking(data,user,booking_id)
            revision=row.get('counterPaymentRevision',0)
            if type(body['version']) is not int or body['version']!=row.get('counterVersion',1):return JsonResponse({'error':'Booking đã đổi. Mở lại chi tiết.'},status=409)
            if type(body['paymentRevision']) is not int:raise ValueError('Phiên thanh toán không hợp lệ.')
            if row.get('counterPaymentFlow')!='manual_confirmation_v1':raise ValueError('Booking cũ cần quản trị đối soát theo lịch sử thu tiền.')
            if any(p.get('provider') for p in row.get('payments',[])) or str(row.get('counterPaymentConfirmedBy','')).startswith('SePay'):
                raise ValueError('Khoản thu SePay đã xác nhận cần đối soát riêng; không thể đưa về chưa thanh toán bằng thao tác này.')
            if payment_pending(row):
                last=row.get('counterHistory',[])[-1] if row.get('counterHistory') else {}
                if last.get('action')=='payment_reopen' and body['paymentRevision']==revision-1 and row.get('paymentMethod')==method:
                    return JsonResponse({'booking':public_booking(row),'duplicate':True})
                raise ValueError('Booking đang chờ thanh toán; không có xác nhận để hủy.')
            if body['paymentRevision']!=revision:return JsonResponse({'error':'Trạng thái thu tiền đã đổi. Mở lại chi tiết.'},status=409)
            before=public_booking(row);old=copy.deepcopy(row.get('payments',[]));now=timezone.now().isoformat()
            row.update(payments=[],status='pending_payment',paymentMethod=method,counterPaymentConfirmedAt=None,counterPaymentConfirmedBy=None,counterPaymentRevision=revision+1)
            if row.get('sepayIntentId'):
                from .models import SePayIntent
                SePayIntent.objects.filter(pk=row['sepayIntentId'],state__in=['pending','expired']).update(state='cancelled')
                row['sepayIntentId']=None
            calculate_booking(row)
            row.setdefault('counterHistory',[]).append({'action':'payment_reopen','at':now,'by':user.get_username(),'reason':reason.strip(),'before':before,'after':public_booking(row),'paymentAdjustment':-float(sum(amount(p['amount']) for p in old)),'paymentsBefore':old,'paymentsAfter':[]})
            save_workspace(obj,data,user,obj.revision,'counter.payment_reopen')
        return JsonResponse({'booking':public_booking(row),'duplicate':False})
    except (RuntimeError,OperationalError):return JsonResponse({'error':'Có thao tác khác đang lưu. Mở lại booking để kiểm tra.'},status=409)
    except (ValueError,TypeError,KeyError,AttributeError) as exc:return JsonResponse({'error':str(exc) or 'Dữ liệu chưa hợp lệ.'},status=400)
