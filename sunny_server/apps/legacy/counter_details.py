"""Versioned, own-booking edits. No client-controlled costs, dates or receipts."""
import copy
import json
import uuid
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction, OperationalError
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .counter import permitted, public_booking, default_cost, payment_pending, PAYMENT_METHODS
from .models import Workspace
from .operations import save_workspace
from .pricing import amount, calculate_booking
from .ticket_lifecycle import enforce_ticket_lifecycle

def own_booking(data,user,key):
    row=next((b for b in data.get('bookings',[]) if b.get('id')==key and b.get('source')=='counter' and (user.is_superuser or b.get('counterSellerId')==user.pk)),None)
    if row is None:raise Http404()
    return row

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def booking_detail(request,booking_id):
    user=request.user
    if not permitted(user,'view') or request.method=='POST' and not permitted(user,'change'):
        return JsonResponse({'error':'Chưa được cấp quyền xem/sửa booking quầy.'},status=403)
    obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data);row=own_booking(data,user,booking_id)
    if request.method=='GET':
        from .sepay import active_intent
        sepay_active=bool(row.get('sepayIntentId') and active_intent(row))
        return JsonResponse({'sepayActive':sepay_active,'booking':public_booking(row),'version':row.get('counterVersion',1),'canConfirmPayment':permitted(user,'create'),'canChange':permitted(user,'change'),'canSettle':permitted(user,'settle_adjustment'),'history':row.get('counterHistory',[])})
    try:
        body=json.loads(request.body)
        if set(body)-{'version','values','settled'}:raise ValueError('Có trường không được phép.')
        if body['version']!=row.get('counterVersion',1):return JsonResponse({'error':'Booking đã thay đổi. Mở lại chi tiết trước khi sửa.'},status=409)
        values=body['values']
        if not isinstance(values,dict) or set(values)-{'ticketId','qty','sellPrice','hasVat','note','customerEmail','paymentMethod'}:raise ValueError('Có trường không được phép.')
        before=public_booking(row);old_payments=copy.deepcopy(row.get('payments',[]))
        pending_before=payment_pending(row)
        if 'paymentMethod' in values:
            if not isinstance(values['paymentMethod'],str) or values['paymentMethod'] not in PAYMENT_METHODS:raise ValueError('Phương thức thanh toán không hợp lệ.')
            if not pending_before and values['paymentMethod']!=row.get('paymentMethod',''):raise ValueError('Không đổi phương thức của khoản thu đã ghi nhận.')
        row.update(values)
        qty=amount(row['qty']);price=amount(row['sellPrice'])
        if qty<=0 or qty>10000 or qty!=int(qty) or price!=int(price):raise ValueError('Số lượng/giá bán không hợp lệ.')
        if not isinstance(row.get('hasVat'),bool) or not isinstance(row.get('note',''),str) or len(row.get('note',''))>2000:raise ValueError('VAT/ghi chú không hợp lệ.')
        email=row.get('customerEmail','').strip()
        if email:validate_email(email)
        if len(email)>254:raise ValueError('Email quá dài.')
        row['customerEmail']=email;row['qty']=int(qty);row['sellPrice']=float(price);row['vatRate']=15 if row['hasVat'] else 0
        ticket=next((t for t in data.get('ticketTypes',[]) if t.get('id')==row['ticketId'] and t.get('active',True)),None)
        if not ticket:raise ValueError('Loại vé không còn hoạt động.')
        if row['ticketId']!=before['ticketId']:
            cost=default_cost(data,row['ticketId'],row['date'])
            row.update(buyPrice=float(amount(cost['price'])),costPriceId=cost['id'],supplierId=cost['supplierId'],supplierName=cost['supplierName'],costSource='supplier')
        row.update(ticketType=ticket.get('name',''),product=ticket.get('product',''))
        row['payments']=[];calculate_booking(row);row['payments']=copy.deepcopy(old_payments)
        paid=sum(amount(p['amount']) for p in old_payments);delta=amount(row['revenue'])-paid
        total_changed=row['revenue']!=before['revenue']
        adjustment=0
        if total_changed and delta and not pending_before:
            if not permitted(user,'settle_adjustment') or body.get('settled') is not True:
                raise ValueError('Tổng tiền thay đổi: cần quyền điều chỉnh thanh toán và xác nhận đã thu thêm/hoàn lại thực tế.')
            adjustment=float(delta)
            if delta>0:row['payments'].append({'id':str(uuid.uuid4()),'date':timezone.localdate().isoformat(),'amount':float(delta),'method':row.get('paymentMethod',''),'note':'Thu thêm khi sửa tại quầy','createdBy':user.pk})
            else:
                remaining=-delta
                for payment in reversed(row['payments']):
                    reduction=min(amount(payment['amount']),remaining);payment['amount']=float(amount(payment['amount'])-reduction);remaining-=reduction
                row['payments']=[p for p in row['payments'] if p['amount']>0]
        calculate_booking(row)
        if pending_before:row['status']='pending_payment'
        row['counterVersion']=row.get('counterVersion',1)+1
        cancelled_intent=row.get('sepayIntentId') if pending_before else None
        if cancelled_intent:row['sepayIntentId']=None
        row.setdefault('counterHistory',[]).append({'at':timezone.now().isoformat(),'by':user.get_username(),'before':before,'after':public_booking(row),'paymentAdjustment':adjustment,'paymentsBefore':old_payments,'paymentsAfter':copy.deepcopy(row['payments'])})
        enforce_ticket_lifecycle(obj.data,data)
        with transaction.atomic():
            if cancelled_intent:
                from .models import SePayIntent
                SePayIntent.objects.filter(pk=cancelled_intent,state='pending').update(state='cancelled')
            save_workspace(obj,data,user,obj.revision,'counter.booking_change')
        return JsonResponse({'booking':public_booking(row),'version':row['counterVersion']})
    except (RuntimeError,OperationalError):return JsonResponse({'error':'Dữ liệu đã đổi. Mở lại chi tiết, không lưu đè.'},status=409)
    except (ValueError,KeyError,TypeError,AttributeError,ValidationError) as exc:return JsonResponse({'error':str(exc) or 'Thông tin chưa hợp lệ.'},status=400)
