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


def booking_row(order,event,intent):
    ticket=order.snapshot['ticket'];cost=order.snapshot['cost'];now=timezone.now().isoformat()
    row={'id':'ONLINE-'+str(order.pk),'bookingCode':order.code,'date':order.visit_date.isoformat(),'createdAt':order.created_at.isoformat(),'source':'counter','salesChannel':'online','counterSellerId':intent.owner_id,'counterVersion':1,'counterPaymentRevision':0,'counterPaymentFlow':'manual_confirmation_v1','counterPaymentConfirmedAt':now,'counterPaymentConfirmedBy':'SePay online','status':'completed','customerType':'retail','agent':'Khách online','customerName':order.customer_name,'ticketId':ticket['id'],'ticketType':ticket.get('name',''),'product':ticket.get('product',''),'qty':order.qty,'sellPrice':order.unit_price,'buyPrice':cost['price'],'cost':0,'costSource':'supplier','costPriceId':cost['id'],'supplierId':cost['supplierId'],'supplierName':cost['supplierName'],'customerEmail':order.email,'note':'Đơn online '+order.code+' · '+order.phone,'hasVat':False,'vatRate':0,'paymentMethod':'bank_transfer','supplierPayments':[],'payments':[{'id':'SEPAY-'+event.pk+'-'+order.id.hex[:12],'date':timezone.localtime(event.transaction_at).date().isoformat(),'amount':order.total,'method':'bank_transfer','provider':'sepay_test' if intent.mode=='test' else 'sepay','providerTransactionId':event.pk,'referenceCode':event.reference_code,'createdAt':now}]}
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
    from django.core.mail import EmailMessage
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
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
        url=settings.PUBLIC_SITE_URL+'/online/staff/cart/'+str(order.pk)+'/'
        message=EmailMessage('Sunny: đơn '+order.code+' đã thanh toán — cần gửi vé',f'Đơn {order.code} đã nhận đủ tiền. Vào trang quản trị để kiểm tra và gửi vé cho khách.\n{url}',to=[address])
        if message.send()!=1:raise ValueError('Email not accepted')
        CartOrder.objects.filter(pk=key).update(notification_state='sent')
    except Exception:
        # Email failure must never roll back an already committed bank receipt.
        CartOrder.objects.filter(pk=key).update(notification_state='error')
