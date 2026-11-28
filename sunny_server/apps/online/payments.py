import copy
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from apps.legacy.models import Workspace
from apps.legacy.pricing import calculate_booking
from apps.legacy.sepay import bank_key
from apps.legacy.operations import save_workspace
from .models import OnlineOrder

def apply_event(event,intent):
    order=OnlineOrder.objects.select_for_update().filter(intent=intent,cart__isnull=True).first()
    if intent.mode!=settings.SEPAY_MODE:return 'Môi trường thanh toán đã đổi; cần đối soát.'
    if bank_key(event.gateway)!=bank_key(intent.gateway) or event.account_number!=intent.account_number:return 'Sai ngân hàng hoặc tài khoản nhận.'
    if event.amount!=intent.amount or event.amount!=event.amount.to_integral_value():return 'Số tiền thiếu/thừa; cần đối soát.'
    if intent.state not in ('pending','expired'):return 'Phiên QR không còn chờ thanh toán.'
    if not event.transaction_at or event.transaction_at<intent.created_at-timedelta(seconds=60) or event.transaction_at>intent.expires_at:return 'Giao dịch ngoài thời gian phiên; cần đối soát.'
    if not order or order.status!='pending' or order.total!=event.amount or order.fingerprint!=intent.booking_fingerprint:return 'Đơn online đã đổi hoặc đã thanh toán.'
    obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data)
    row=booking_row(order,event,intent)
    if any(b.get('id')==row['id'] for b in data.get('bookings',[])):return 'Booking online đã tồn tại; cần đối soát.'
    calculate_booking(row);data.setdefault('bookings',[]).append(row)
    save_workspace(obj,data,None,obj.revision,'online.sepay_paid')
    order.status='paid';order.paid_at=event.transaction_at;order.booking_id=row['id'];order.save(update_fields=['status','paid_at','booking_id'])
    intent.state='paid';intent.paid_at=timezone.now();intent.save(update_fields=['state','paid_at']);event.state='applied'
    return 'Đơn online đã thanh toán; chờ nhân viên gửi vé.'


def booking_row(order,event,intent,*,cash_user=None,paid_at=None):
    ticket=order.snapshot['ticket'];cost=order.snapshot['cost'];now=timezone.now().isoformat()
    if cash_user:
        seller_id=cash_user.pk;confirmed_by=cash_user.username;method='cash'
        payment=[{'id':'CASH-'+str(order.pk),'date':timezone.localtime(paid_at).date().isoformat(),'amount':order.total,'method':'cash','provider':'manual','createdAt':now}]
    else:
        seller_id=intent.owner_id;confirmed_by='SePay online';method='bank_transfer'
        payment=[{'id':'SEPAY-'+event.pk+'-'+order.id.hex[:12],'date':timezone.localtime(event.transaction_at).date().isoformat(),'amount':order.total,'method':'bank_transfer','provider':'sepay_test' if intent.mode=='test' else 'sepay','providerTransactionId':event.pk,'referenceCode':event.reference_code,'createdAt':now}]
    row={'id':'ONLINE-'+str(order.pk),'bookingCode':order.code,'date':order.visit_date.isoformat(),'createdAt':order.created_at.isoformat(),'source':'counter','salesChannel':'online','counterSellerId':seller_id,'counterVersion':1,'counterPaymentRevision':0,'counterPaymentFlow':'manual_confirmation_v1','counterPaymentConfirmedAt':now,'counterPaymentConfirmedBy':confirmed_by,'status':'completed','customerType':'retail','agent':'Digital','customerName':order.customer_name,'ticketId':ticket['id'],'ticketType':ticket.get('name',''),'product':ticket.get('product',''),'qty':order.qty,'sellPrice':order.unit_price,'buyPrice':cost['price'],'cost':0,'costSource':'supplier','costPriceId':cost['id'],'supplierId':cost['supplierId'],'supplierName':cost['supplierName'],'customerEmail':order.email,'note':'Đơn online '+order.code+' · '+order.phone,'hasVat':False,'vatRate':0,'paymentMethod':method,'supplierPayments':[],'payments':payment}
    return row


def apply_cart_event(event,intent):
    from django.db import transaction
    from .models import CartOrder
    order=CartOrder.objects.select_for_update().filter(intent=intent).first()
    if intent.mode!=settings.SEPAY_MODE:return 'Môi trường thanh toán đã đổi; cần đối soát.'
    if bank_key(event.gateway)!=bank_key(intent.gateway) or event.account_number!=intent.account_number:return 'Sai ngân hàng hoặc tài khoản nhận.'
    if event.amount!=intent.amount or event.amount!=event.amount.to_integral_value():return 'Số tiền thiếu/thừa; cần đối soát.'
    if intent.state not in ('pending','expired'):return 'Phiên QR không còn chờ thanh toán.'
    if not event.transaction_at or event.transaction_at<intent.created_at-timedelta(seconds=60) or event.transaction_at>intent.expires_at:return 'Giao dịch ngoài thời gian phiên; cần đối soát.'
    if not order or order.status!='pending' or order.total!=event.amount or order.fingerprint!=intent.booking_fingerprint:return 'Đơn đã đổi hoặc đã thanh toán.'
    lines=list(order.lines.select_for_update().all())
    if not lines or sum(line.total for line in lines)!=order.total or any(line.status!='pending' or line.total!=line.unit_price*line.qty for line in lines):return 'Chi tiết đơn cần đối soát.'
    obj=Workspace.objects.get(pk=1);data=copy.deepcopy(obj.data)
    rows=[booking_row(line,event,intent) for line in lines]
    ids={row.get('id') for row in data.get('bookings',[])}
    if any(row['id'] in ids for row in rows):return 'Booking đã tồn tại; cần đối soát.'
    for line,row in zip(lines,rows):
        row['onlineCartId']=str(order.pk);row['onlineCartCode']=order.code;row['note']='Đơn giỏ hàng '+order.code+' · '+order.phone
        calculate_booking(row);data.setdefault('bookings',[]).append(row)
        line.status='paid';line.paid_at=event.transaction_at;line.booking_id=row['id'];line.save(update_fields=['status','paid_at','booking_id'])
    save_workspace(obj,data,None,obj.revision,'online.cart_paid')
    order.status='paid';order.paid_at=event.transaction_at;order.save(update_fields=['status','paid_at'])
    intent.state='paid';intent.paid_at=timezone.now();intent.save(update_fields=['state','paid_at']);event.state='applied'
    transaction.on_commit(lambda:notify_admin(order.pk))
    return 'Đơn giỏ hàng đã thanh toán; chờ quản trị gửi vé.'


def notify_admin(key):
    from django.core.validators import validate_email
    from .models import CartOrder
    try:
        order=CartOrder.objects.get(pk=key)
        address=getattr(settings,'ONLINE_ADMIN_EMAIL','')
        if not address:
            from .views import owner
            account=owner();address=account.email if account else ''
        if not address:
            CartOrder.objects.filter(pk=key).update(notification_state='unconfigured');return
        validate_email(address)
        if order.status!='paid' and not (order.status=='pending' and order.payment_method=='cash' and order.cash_requested_at):return
        from .booking_email import booking_notification
        message=booking_notification(order,address)
        if message.send()!=1:raise ValueError('Email not accepted')
        CartOrder.objects.filter(pk=key).update(notification_state='sent')
    except Exception:
        # Email failure must never roll back an already committed bank receipt.
        CartOrder.objects.filter(pk=key).update(notification_state='error')


def collect_cash(order,user,amount,note):
    """Called inside an atomic order lock, only after staff confirms physical delivery."""
    from .models import CartOrder
    from apps.audit.models import AuditLog
    if not user.is_active or not (user.is_superuser or user.has_perm('online.collect_cash_orders')):raise ValueError('Chưa có quyền xác nhận thu tiền mặt đơn online.')
    if order.status!='pending' or order.payment_method!='cash' or not order.cash_requested_at or order.intent_id:raise ValueError('Đơn không còn chờ giao vé và thu tiền mặt.')
    if str(amount)!=str(order.total):raise ValueError('Số tiền thực thu phải đúng tổng đơn.')
    if not 10<=len(note)<=1000:raise ValueError('Nhập ghi chú xác nhận giao vé và thu tiền từ 10 đến 1000 ký tự.')
    lines=list(order.lines.select_for_update().all())
    if not lines or sum(line.total for line in lines)!=order.total or any(line.status!='pending' or line.qty<1 or line.total!=line.unit_price*line.qty for line in lines):raise ValueError('Chi tiết đơn cần đối soát.')
    if any(line.visit_date<timezone.localdate() for line in lines):raise ValueError('Ngày sử dụng đã qua; cần quản trị đối soát trước khi thu tiền.')
    obj=Workspace.objects.select_for_update().get(pk=1);data=copy.deepcopy(obj.data);now=timezone.now()
    ids={row.get('id') for row in data.get('bookings',[])}
    for line in lines:
        row=booking_row(line,None,None,cash_user=user,paid_at=now)
        if row['id'] in ids:raise ValueError('Booking đã tồn tại; cần đối soát.')
        row['onlineCartId']=str(order.pk);row['onlineCartCode']=order.code
        row['note']='Giao vé / thu tiền mặt tại Đà Nẵng · '+order.code+' · '+order.phone
        calculate_booking(row);data.setdefault('bookings',[]).append(row)
        line.status='paid';line.paid_at=now;line.booking_id=row['id'];line.save(update_fields=['status','paid_at','booking_id'])
    save_workspace(obj,data,user,obj.revision,'online.cash_collected')
    order.status='paid';order.paid_at=now;order.email_state='external';order.emailed_at=now;order.processed_by=user;order.processing_note=note
    order.save(update_fields=['status','paid_at','email_state','emailed_at','processed_by','processing_note'])
    AuditLog.objects.create(user=user,action='online.cash.delivered_collected:'+order.code)
