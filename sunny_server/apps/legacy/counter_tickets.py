import hashlib
import json
import os
from pathlib import Path
import tempfile
from io import BytesIO
import zipfile
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.db import transaction, IntegrityError, OperationalError
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_sameorigin
from .counter import permitted
from .models import Workspace, CounterTicketBatch, CounterIssuedQR
from .ticket_processing import extract_tickets, checked_fields, render_tickets, FIELDS

def email_ready():
    return bool(getattr(settings,'COUNTER_EMAIL_ENABLED',False) and settings.DEFAULT_FROM_EMAIL and (settings.EMAIL_BACKEND!='django.core.mail.backends.smtp.EmailBackend' or settings.EMAIL_HOST))

def root():
    path=Path(getattr(settings,'COUNTER_PRIVATE_ROOT',Path(settings.BASE_DIR)/'private_counter')).resolve();path.mkdir(parents=True,exist_ok=True,mode=0o700);return path

def directory(batch):
    path=root()/str(batch.pk);path.mkdir(exist_ok=True,mode=0o700);return path

def write(path,blob):
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as file:
        temporary=Path(file.name);file.write(blob)
    os.chmod(temporary,0o600);temporary.replace(path)

def booking_for(user,key):
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    matches=[b for b in data.get('bookings',[]) if b.get('id')==key and b.get('source')=='counter' and (user.is_superuser or b.get('counterSellerId')==user.pk)]
    if len(matches)!=1:raise Http404()
    return matches[0]

def allowed_batch(request,key,create=False):
    if not permitted(request.user,'view') or create and not permitted(request.user,'create'):raise Http404()
    query=CounterTicketBatch.objects.all() if request.user.is_superuser else CounterTicketBatch.objects.filter(owner=request.user)
    batch=get_object_or_404(query,pk=key);booking=booking_for(request.user,batch.booking_id);return batch,booking

def needs_replacement(booking):
    return CounterTicketBatch.objects.filter(booking_id=booking['id']).exclude(output_hash='').exists()

def require_replacement(user,booking):
    if needs_replacement(booking) and not permitted(user,'replace_tickets'):
        raise ValueError('Cần quyền thay bộ vé để tạo phiên bản mới. Bộ vé cũ vẫn được giữ.')

def public_batch(batch,booking):
    return {'id':str(batch.pk),'name':batch.source_name,'bookingId':batch.booking_id,'quantity':booking['qty'],'ready':bool(batch.output_hash),'email':batch.customer_email,'emailState':batch.email_state,
            'emailEnabled':email_ready() and not batch.superseded_at and batch.booking_version==booking.get('counterVersion',1), 'selected':batch.selected,
            'archived':bool(batch.superseded_at) or batch.booking_version!=booking.get('counterVersion',1),'createdAt':batch.created_at.isoformat(),
            'rows':[{'page':r['page'],'sourcePage':r.get('source_page',r['page']),**{k:r.get(k,'') for k in FIELDS},'qrUrl':f'/api/counter/ticket-batches/{batch.pk}/qr/{r["page"]}/'} for r in batch.rows]}

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def booking_tickets(request,booking_id):
    if not permitted(request.user,'view') or request.method=='POST' and not permitted(request.user,'create'):return JsonResponse({'error':'Không có quyền nhập vé.'},status=403)
    booking=booking_for(request.user,booking_id)
    if request.method=='GET':
        batches=CounterTicketBatch.objects.filter(booking_id=booking_id).order_by('-created_at')
        if not request.user.is_superuser:batches=batches.filter(owner=request.user)
        return JsonResponse({'booking':{'code':booking['bookingCode'],'qty':booking['qty'],'email':booking.get('customerEmail','')},'canReplace':permitted(request.user,'replace_tickets'),'batches':[public_batch(b,booking) for b in batches]})
    uploads=request.FILES.getlist('files') or request.FILES.getlist('file')
    if not uploads or len(uploads)>20 or not 0<sum(f.size for f in uploads)<=20*1024*1024:return JsonResponse({'error':'Chọn tối đa 20 file PDF/JPEG/PNG, tổng tối đa 20 MB.'},status=400)
    sources=[(Path(f.name).name[:255],f.read()) for f in uploads]
    digest=hashlib.sha256(json.dumps([(name,hashlib.sha256(blob).hexdigest()) for name,blob in sources]).encode()).hexdigest()
    existing=CounterTicketBatch.objects.filter(owner=request.user,booking_id=booking_id,source_hash=digest).first()
    if existing:return JsonResponse(public_batch(existing,booking))
    try:
        require_replacement(request.user,booking)
        rows=[]
        for source_index,(name,blob) in enumerate(sources,1):
            extracted=extract_tickets(blob)
            for row in extracted:
                row['source_index']=source_index;row.setdefault('source_page',row['page']);row['source_name']=name;row['page']=len(rows)+1;rows.append(row)
            if len(rows)>50:raise ValueError('Tối đa 50 vé trong một đợt nhập.')
        if len({r['qr_hash'] for r in rows})!=len(rows):raise ValueError('Các file có QR trùng nhau. Chưa nhập bộ vé.')
        stream=BytesIO()
        if len(sources)>1:
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
                for i,(name,blob) in enumerate(sources):archive.writestr('source-'+str(i+1)+Path(name).suffix,blob)
        source_blob=sources[0][1] if len(sources)==1 else stream.getvalue()
        with transaction.atomic():
            batch=CounterTicketBatch.objects.create(owner=request.user,booking_id=booking_id,booking_version=booking.get('counterVersion',1),source_name=sources[0][0] if len(sources)==1 else str(len(sources))+' files',source_hash=digest,customer_email=booking.get('customerEmail',''))
            folder=directory(batch);write(folder/'source',source_blob)
            for i,(name,blob) in enumerate(sources):write(folder/('original-'+str(i+1)),blob)
            for row in rows:write(folder/(str(row['page'])+'.png'),row.pop('qr_png'))
            batch.rows=rows;batch.save(update_fields=['rows'])
        return JsonResponse(public_batch(batch,booking),status=201)
    except IntegrityError:
        batch=CounterTicketBatch.objects.filter(owner=request.user,booking_id=booking_id,source_hash=digest).first()
        if batch:return JsonResponse(public_batch(batch,booking))
        return JsonResponse({'error':'Có giao dịch khác đang xử lý. Hãy tải lại danh sách vé.'},status=409)
    except Exception as exc:
        message=str(exc) if isinstance(exc,ValueError) else 'Không đọc được file vé. Hãy dùng PDF không khóa hoặc ảnh JPEG/PNG rõ QR.'
        return JsonResponse({'error':message},status=400)

@login_required
@never_cache
@require_http_methods(['GET'])
def ticket_qr(request,batch_id,page):
    batch,_=allowed_batch(request,batch_id)
    if page not in [r['page'] for r in batch.rows]:raise Http404()
    path=directory(batch)/(str(page)+'.png')
    if not path.is_file():raise Http404()
    return FileResponse(path.open('rb'),content_type='image/png')

@login_required
@never_cache
@require_http_methods(['POST'])
def generate_tickets(request,batch_id):
    batch,booking=allowed_batch(request,batch_id,True)
    try:
        body=json.loads(request.body)
        if batch.booking_version!=booking.get('counterVersion',1) or batch.superseded_at:raise ValueError('Phiên bản vé cũ. Tạo phiên bản mới theo booking hiện tại.')
        if body.get('confirmed') is not True:raise ValueError('Xác nhận đã kiểm tra QR/thông tin/ngày sử dụng trước khi xuất.')
        requested=body['rows']
        if not isinstance(requested,list):raise ValueError('Danh sách vé được chọn không hợp lệ.')
        if len(requested)!=int(booking['qty']):raise ValueError(f"Booking {booking.get('bookingCode',booking['id'])}: {booking['qty']} vé, đã chọn {len(requested)} vé. Chỉ xuất khi chọn đúng số lượng booking.")
        by_page={r['page']:r for r in batch.rows};seen=set();selected=[]
        for row in requested:
            page=row['page']
            if page in seen or page not in by_page:raise ValueError('Trang vé không hợp lệ hoặc bị chọn trùng.')
            seen.add(page);selected.append({'page':page,'qr_hash':by_page[page]['qr_hash'],**checked_fields(row)})
        if len({r['qr_hash'] for r in selected})!=len(selected):raise ValueError('Không xuất QR trùng.')
        if batch.output_hash:
            if selected!=batch.selected:raise ValueError('Bộ vé đã xác nhận được giữ cố định. Dùng lại PDF đã xuất; liên hệ quản trị nếu cần đối soát.')
            return JsonResponse({'pdfUrl':f'/api/counter/ticket-batches/{batch.pk}/pdf/'})
        folder=directory(batch);pdf=render_tickets(selected,[(folder/(str(r['page'])+'.png')).read_bytes() for r in selected])
        with transaction.atomic():
            # Lock workspace with a no-op write, serializing assignments even on SQLite.
            Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            booking=booking_for(request.user,batch.booking_id)
            if len(selected)!=int(booking['qty']):raise ValueError('Số lượng booking vừa thay đổi. Hãy mở lại bộ vé.')
            batch=CounterTicketBatch.objects.select_for_update().get(pk=batch.pk)
            if batch.output_hash:
                if selected!=batch.selected:raise ValueError('Bộ vé đã được xác nhận trong phiên khác.')
            else:
                require_replacement(request.user,booking)
                if batch.booking_version!=booking.get('counterVersion',1):raise ValueError('Booking vừa thay đổi. Tạo phiên bản mới.')
                existing=set(CounterIssuedQR.objects.filter(booking_id=batch.booking_id).values_list('qr_hash',flat=True));hashes={r['qr_hash'] for r in selected}
                for row in selected:
                    issued,created=CounterIssuedQR.objects.get_or_create(qr_hash=row['qr_hash'],defaults={'booking_id':batch.booking_id,'batch':batch})
                    if issued.booking_id!=batch.booking_id:
                        workspace=Workspace.objects.get(pk=1).data
                        linked=next((b for b in workspace.get('bookings',[]) if b.get('id')==issued.booking_id),None)
                        label=linked.get('bookingCode') if linked else None
                        raise ValueError('QR đã được gắn cho booking '+str(label or issued.booking_id)+'. Chưa xuất bộ vé này.')
                write(folder/'tickets.pdf',pdf);batch.selected=selected;batch.output_hash=hashlib.sha256(pdf).hexdigest();batch.save(update_fields=['selected','output_hash'])
                CounterTicketBatch.objects.filter(booking_id=batch.booking_id,superseded_at__isnull=True).exclude(pk=batch.pk).exclude(output_hash='').update(superseded_at=timezone.now())
                from apps.audit.models import AuditLog
                AuditLog.objects.create(user=request.user,action='counter.tickets_issue:'+str(batch.pk),revision=Workspace.objects.get(pk=1).revision)
        return JsonResponse({'pdfUrl':f'/api/counter/ticket-batches/{batch.pk}/pdf/'})
    except (ValueError,TypeError,KeyError) as exc:return JsonResponse({'error':str(exc) or 'Dữ liệu vé không hợp lệ.'},status=400)
    except (OperationalError,IntegrityError):return JsonResponse({'error':'Có phiên khác đang xuất vé. Hãy mở lại bộ vé để kiểm tra.'},status=409)

def output_bytes(batch):
    path=directory(batch)/'tickets.pdf'
    if not batch.output_hash or not path.is_file():raise Http404()
    blob=path.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=batch.output_hash:raise Http404()
    return blob

@login_required
@never_cache
@require_http_methods(['GET'])
@xframe_options_sameorigin
def tickets_pdf(request,batch_id):
    from io import BytesIO
    batch,_=allowed_batch(request,batch_id);blob=output_bytes(batch)
    return FileResponse(BytesIO(blob),content_type='application/pdf',as_attachment=request.GET.get('download')=='1',filename='ve-80x110-'+str(batch.pk)+'.pdf')

@login_required
@never_cache
@require_http_methods(['POST'])
def email_tickets(request,batch_id):
    batch,booking=allowed_batch(request,batch_id,True)
    if batch.superseded_at or batch.booking_version!=booking.get('counterVersion',1):return JsonResponse({'error':'Không gửi email phiên bản vé cũ.'},status=409)
    if not email_ready():return JsonResponse({'error':'Chưa cấu hình hộp thư gửi. Bạn vẫn có thể xuất PDF hoặc in vé.'},status=400)
    blob=output_bytes(batch)
    try:
        body=json.loads(request.body);email=body['email'].strip();validate_email(email)
        if len(email)>254:raise ValueError('Email quá dài.')
        if body.get('confirmed') is not True:raise ValueError('Xác nhận địa chỉ người nhận trước khi gửi.')
    except (ValueError,KeyError,TypeError,AttributeError,ValidationError):return JsonResponse({'error':'Kiểm tra địa chỉ email và xác nhận người nhận.'},status=400)
    if batch.email_state=='sent' and batch.customer_email==email:return JsonResponse({'status':'sent','alreadySent':True})
    if not CounterTicketBatch.objects.filter(pk=batch.pk,email_state='idle').update(email_state='sending',customer_email=email):return JsonResponse({'error':'Đợt này đã gửi hoặc kết quả gửi đang cần đối soát. Không gửi lại tự động.'},status=409)
    try:
        message=EmailMessage('Vé '+booking['bookingCode']+' - Sunny Travel','Kính gửi Quý khách,\n\nVé của Quý khách được đính kèm trong email này. Vui lòng kiểm tra thông tin và ngày sử dụng trên vé.\n\nSunny Travel',to=[email])
        message.attach('ve-'+booking['bookingCode']+'.pdf',blob,'application/pdf')
        if message.send(fail_silently=False)!=1:raise RuntimeError('Not accepted')
        CounterTicketBatch.objects.filter(pk=batch.pk).update(email_state='sent',emailed_at=timezone.now())
        return JsonResponse({'status':'sent','alreadySent':False})
    except Exception:
        CounterTicketBatch.objects.filter(pk=batch.pk).update(email_state='uncertain')
        return JsonResponse({'error':'Chưa xác nhận máy chủ thư đã tiếp nhận. Liên hệ quản trị kiểm tra trước khi gửi lại để tránh trùng.'},status=502)

@login_required
@never_cache
@require_http_methods(['POST'])
def replace_tickets(request,batch_id):
    batch,booking=allowed_batch(request,batch_id,True)
    if not permitted(request.user,'replace_tickets'):return JsonResponse({'error':'Chưa có quyền thay bộ vé.'},status=403)
    with transaction.atomic():
        replacement=CounterTicketBatch.objects.create(owner=request.user,booking_id=batch.booking_id,booking_version=booking.get('counterVersion',1),source_name=batch.source_name,source_hash=hashlib.sha256((batch.source_hash+str(uuid.uuid4())).encode()).hexdigest(),rows=batch.rows,customer_email=booking.get('customerEmail',''))
        target=directory(replacement)
        for file in directory(batch).iterdir():
            if file.name=='source' or file.name.startswith('original-') or file.suffix=='.png':write(target/file.name,file.read_bytes())
    return JsonResponse(public_batch(replacement,booking),status=201)

@login_required
@never_cache
@require_http_methods(['POST'])
def reread_tickets(request,batch_id):
    batch,booking=allowed_batch(request,batch_id,True)
    if batch.output_hash:return JsonResponse({'error':'Bộ vé đã xuất được giữ nguyên. Tạo phiên bản mới trước khi đọc lại.'},status=409)
    try:
        require_replacement(request.user,booking)
        folder=directory(batch);sources=sorted(folder.glob('original-*'),key=lambda p:int(p.name.split('-')[-1]))
        blobs=[p.read_bytes() for p in sources]
        if not blobs:
            blob=(folder/'source').read_bytes()
            if blob.startswith(b'PK'):
                with zipfile.ZipFile(BytesIO(blob)) as archive:
                    if len(archive.infolist())>20 or sum(i.file_size for i in archive.infolist())>20*1024*1024:raise ValueError('Nguồn lưu trữ quá lớn.')
                    blobs=[archive.read(info) for info in archive.infolist()]
            else:blobs=[blob]
        rows=[]
        for source_index,blob in enumerate(blobs,1):
            for row in extract_tickets(blob):
                row.setdefault('source_page',row['page']);row['source_index']=source_index;row['page']=len(rows)+1;row.pop('qr_png')
                original=next((r for r in batch.rows if r['qr_hash']==row['qr_hash']),{})
                row['source_name']=original.get('source_name',batch.source_name);rows.append(row)
                if len(rows)>50:raise ValueError('Tối đa 50 vé.')
        if [r['qr_hash'] for r in rows]!=[r['qr_hash'] for r in batch.rows]:raise ValueError('QR/thứ tự vé thay đổi khi đọc lại. Chưa cập nhật; cần nhập thành bộ mới để kiểm tra.')
        with transaction.atomic():
            current=CounterTicketBatch.objects.select_for_update().get(pk=batch.pk)
            if current.output_hash:return JsonResponse({'error':'Bộ vé vừa được xuất trong phiên khác. Chưa thay đổi.'},status=409)
            current.rows=rows;current.save(update_fields=['rows'])
        return JsonResponse(public_batch(current,booking))
    except Exception as exc:
        return JsonResponse({'error':str(exc) if isinstance(exc,ValueError) else 'Không đọc lại được nguồn. Kiểm tra OCR hoặc nhập bộ file mới.'},status=400)
