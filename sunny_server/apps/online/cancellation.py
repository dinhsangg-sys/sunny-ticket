from django.utils import timezone
from apps.legacy.models import Workspace
from apps.audit.models import AuditLog

def cancel_unpaid(order,user,reason):
    """Caller holds the parent order lock inside transaction.atomic()."""
    if not user.is_active or not user.is_superuser:raise ValueError('Chỉ quản trị superuser được hủy đơn online.')
    reason=reason.strip()
    if not 5<=len(reason)<=1000:raise ValueError('Nhập lý do hủy từ 5 đến 1000 ký tự.')
    if order.status=='cancelled':return
    if order.status!='pending' or order.paid_at or order.intent_id or order.email_state!='pending' or order.emailed_at:raise ValueError('Chỉ hủy đơn chưa thu tiền và chưa tạo QR. Đơn có thanh toán/QR phải đối soát riêng.')
    lines=list(order.lines.select_for_update().all())
    if any(line.status!='pending' or line.paid_at or line.booking_id or line.intent_id for line in lines):raise ValueError('Đơn đã có dữ liệu thanh toán/booking; cần đối soát trước khi hủy.')
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    ids={'ONLINE-'+str(line.pk) for line in lines}
    if any(row.get('id') in ids or row.get('onlineCartId')==str(order.pk) for row in data.get('bookings',[])):raise ValueError('Đã tồn tại booking tài chính; cần đối soát riêng.')
    now=timezone.now()
    order.status='cancelled';order.cancelled_at=now;order.cancelled_by=user;order.cancellation_reason=reason
    order.save(update_fields=['status','cancelled_at','cancelled_by','cancellation_reason'])
    order.lines.update(status='cancelled')
    AuditLog.objects.create(user=user,action='online.cart.cancel:'+order.code)
