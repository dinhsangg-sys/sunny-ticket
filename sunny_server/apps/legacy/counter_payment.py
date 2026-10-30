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
from .counter import permitted, public_booking, PAYMENT_METHODS
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
        if not isinstance(body,dict) or set(body)-{'version','paymentMethod','confirmed'} or body.get('confirmed') is not True:raise ValueError('Cần xác nhận đã nhận tiền thực tế.')
        method=body.get('paymentMethod',row.get('paymentMethod','cash'))
        if not isinstance(method,str) or method not in PAYMENT_METHODS:raise ValueError('Phương thức thanh toán không hợp lệ.')
        if row.get('counterPaymentFlow')!='manual_confirmation_v1':raise ValueError('Booking cũ giữ cách ghi nhận thanh toán hiện có; quản trị đối soát nếu cần.')
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
