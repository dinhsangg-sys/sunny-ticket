from io import BytesIO
from pathlib import Path
import pymupdf
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db import transaction,IntegrityError,OperationalError
from django.http import HttpResponseForbidden,FileResponse
from django.shortcuts import get_object_or_404,render,redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods,require_GET
from apps.audit.models import AuditLog
from .models import CartOrder,OrderTicket
from .views import can_process,email_ready
from .cart import state


def checked_file(upload):
    if not 0<upload.size<=10*1024*1024:raise ValueError('Mỗi tệp tối đa 10 MB.')
    raw=upload.read(10*1024*1024+1)
    if len(raw)>10*1024*1024:raise ValueError('Tệp quá lớn.')
    if raw.startswith(b'%PDF-'):
        try:
            with pymupdf.open(stream=raw,filetype='pdf') as doc:
                if doc.is_encrypted or not 1<=doc.page_count<=200:raise ValueError()
        except Exception:raise ValueError('PDF không hợp lệ, có mật khẩu hoặc quá 200 trang.')
        return raw,'.pdf','application/pdf'
    try:
        image=Image.open(BytesIO(raw));image.verify()
        if image.format not in ('JPEG','PNG') or image.width*image.height>25000000:raise ValueError()
        # Re-encode images to discard unrelated payloads and metadata.
        clean=Image.open(BytesIO(raw));stream=BytesIO();clean.save(stream,format=image.format)
        return stream.getvalue(),('.png' if image.format=='PNG' else '.jpg'),('image/png' if image.format=='PNG' else 'image/jpeg')
    except Exception:raise ValueError('Chỉ nhận PDF, PNG hoặc JPEG hợp lệ.')

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def process(request,key):
    if not can_process(request.user):return HttpResponseForbidden('Cần quyền xử lý đơn online và quyền bán vé.')
    order=get_object_or_404(CartOrder,pk=key);error='';message=''
    if request.method=='POST':
        try:
            action=request.POST.get('action')
            with transaction.atomic():
                order=CartOrder.objects.select_for_update().get(pk=key)
                if action=='collect_cash':
                    if not request.POST.get('confirmed'):raise ValueError('Xác nhận đã giao đúng vé và thực nhận đủ tiền mặt.')
                    from .payments import collect_cash
                    collect_cash(order,request.user,request.POST.get('cash_amount',''),request.POST.get('note','').strip())
                    return redirect('online-cart-process',key=key)
                if order.status!='paid' or state(order)=='review':raise ValueError('Đơn chưa thanh toán hoặc đang cần đối soát; chưa được gửi vé.')
                if order.email_state in ('sent','external'):raise ValueError('Đơn đã ghi nhận gửi vé. Không gửi lặp.')
                if order.email_state=='sending' and not (action=='external' and order.can_reconcile):raise ValueError('Email đang gửi. Nếu bị gián đoạn, chờ 5 phút rồi đối soát hộp thư trước khi ghi nhận đã gửi bên ngoài.')
                if action=='remove':
                    if order.email_state!='pending':raise ValueError('Chỉ bỏ tệp trước khi bắt đầu gửi.')
                    ticket=get_object_or_404(OrderTicket,pk=request.POST.get('ticket'),order=order)
                    storage=ticket.file.storage;name=ticket.file.name
                    ticket.delete();transaction.on_commit(lambda:storage.delete(name))
                    AuditLog.objects.create(user=request.user,action='online.cart.remove_ticket:'+order.code)
                    return redirect('online-cart-process',key=key)
                if action=='upload':
                    if order.email_state!='pending':raise ValueError('Kết quả email cần đối soát trước khi đổi tệp.')
                    uploads=request.FILES.getlist('tickets')
                    if not uploads:raise ValueError('Chọn vé cần đính kèm.')
                    existing=list(order.tickets.all())
                    if len(existing)+len(uploads)>8:raise ValueError('Mỗi đơn tối đa 8 tệp.')
                    checked=[(file,*checked_file(file)) for file in uploads]
                    if sum(t.size for t in existing)+sum(len(item[1]) for item in checked)>20*1024*1024:raise ValueError('Tổng tệp tối đa 20 MB.')
                    for upload,raw,ext,mime in checked:
                        name=''.join(c for c in Path(upload.name.replace('\\','/')).stem if c.isprintable())[:150]+ext
                        ticket=OrderTicket(order=order,name=name,extension=ext,content_type=mime,size=len(raw),uploaded_by=request.user)
                        ticket.file.save('ticket'+ext,ContentFile(raw),save=True)
                    AuditLog.objects.create(user=request.user,action='online.cart.upload:'+order.code)
                    return redirect('online-cart-process',key=key)
                if action=='external':
                    note=request.POST.get('note','').strip()
                    if not request.POST.get('confirmed') or len(note)<10 or len(note)>2000:raise ValueError('Xác nhận đã gửi vé bên ngoài và nhập ghi chú đối soát từ 10 đến 2000 ký tự.')
                    order.email_state='external';order.emailed_at=timezone.now();order.processed_by=request.user;order.processing_note=note;order.save(update_fields=['email_state','emailed_at','processed_by','processing_note'])
                    AuditLog.objects.create(user=request.user,action='online.cart.external:'+order.code)
                    return redirect('online-cart-process',key=key)
                if action=='send':
                    if order.email_state!='pending':raise ValueError('Kết quả gửi chưa rõ. Kiểm tra hộp thư trước; không gửi lại tự động.')
                    if not request.POST.get('confirmed'):raise ValueError('Xác nhận đã kiểm tra đúng email và đầy đủ vé cho tất cả dịch vụ.')
                    if not email_ready():raise ValueError('Chưa cấu hình hộp thư gửi.')
                    tickets=list(order.tickets.all())
                    if not tickets:raise ValueError('Đính kèm vé trước khi gửi.')
                    attachments=[]
                    for ticket in tickets:
                        with ticket.file.open('rb') as file:attachments.append((ticket.name,file.read(),ticket.content_type))
                    order.email_state='sending';order.send_started_at=timezone.now();order.processed_by=request.user;order.save(update_fields=['email_state','processed_by','send_started_at'])
                    AuditLog.objects.create(user=request.user,action='online.cart.send_start:'+order.code)
                else:raise ValueError('Thao tác không hợp lệ.')
            # SMTP is outside the DB lock; state is already reserved against duplicate clicks.
            try:
                english=order.language=='en'
                subject=('Your Sunny tickets — ' if english else 'Vé trải nghiệm Sunny — ')+order.code
                body=(f'Hello {order.customer_name},\n\nYour tickets for order {order.code} are attached. Please check the service, visit date and ticket details.\n\nThank you for choosing Sunny.\nHotline: +84 932 548 145' if english else f'Chào {order.customer_name},\n\nSunny gửi vé cho đơn {order.code} trong tệp đính kèm. Vui lòng kiểm tra dịch vụ, ngày sử dụng và thông tin vé.\n\nCảm ơn bạn đã chọn Sunny.\nHotline: +84 932 548 145')
                mail=EmailMessage(subject,body,to=[order.email])
                for item in attachments:mail.attach(*item)
                if mail.send()!=1:raise RuntimeError('Mail not accepted')
            except Exception:
                CartOrder.objects.filter(pk=key,email_state='sending').update(email_state='uncertain')
                error='Chưa xác nhận máy chủ thư đã nhận. Kiểm tra thư đã gửi trước khi thao tác tiếp; hệ thống không tự gửi lại.'
            else:
                CartOrder.objects.filter(pk=key,email_state='sending').update(email_state='sent',emailed_at=timezone.now())
                AuditLog.objects.create(user=request.user,action='online.cart.sent:'+order.code)
                return redirect('online-cart-process',key=key)
        except (ValueError,OSError,RuntimeError) as exc:error=str(exc)
        except (IntegrityError,OperationalError):error='Có thao tác đồng thời. Tải lại để kiểm tra.'
    order.refresh_from_db()
    return render(request,'online/process_cart.html',{'order':order,'lines':order.lines.select_related('service'),'tickets':order.tickets.all(),'error':error,'cash_pending':order.status=='pending' and order.payment_method=='cash' and order.cash_requested_at is not None,'can_collect_cash':request.user.is_superuser or request.user.has_perm('online.collect_cash_orders'),'ready':order.status=='paid' and state(order)!='review','can_send':order.email_state=='pending','can_reconcile':order.can_reconcile})

@login_required
@never_cache
@require_GET
def ticket_file(request,key):
    if not can_process(request.user):return HttpResponseForbidden()
    ticket=get_object_or_404(OrderTicket,pk=key)
    response=FileResponse(ticket.file.open('rb'),as_attachment=True,filename=ticket.name,content_type=ticket.content_type)
    response['X-Content-Type-Options']='nosniff';response['Referrer-Policy']='no-referrer';return response
