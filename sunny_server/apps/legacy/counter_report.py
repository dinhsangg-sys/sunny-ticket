import hashlib
import re
from io import BytesIO
import pymupdf as fitz
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_sameorigin
from .counter import permitted
from .counter_tickets import directory
from .models import Workspace, CounterTicketBatch
from .ticket_processing import FIELDS, decode

def report_allowed(user):return permitted(user,'view') and permitted(user,'report')

def rows_for(user):
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    return [b for b in data.get('bookings',[]) if b.get('source')=='counter' and (user.is_superuser or permitted(user,'report_all') or b.get('counterSellerId')==user.pk)]

def report_batch(user,key):
    if not report_allowed(user):raise Http404()
    batch=get_object_or_404(CounterTicketBatch,pk=key)
    booking=next((b for b in rows_for(user) if b.get('id')==batch.booking_id),None)
    if not booking:raise Http404()
    return batch,booking

def clean(value):return re.sub(r'\s+',' ',str(value or '')).strip()

def comparison(batch,booking,verify=False):
    originals={r['page']:r for r in batch.rows};details=[]
    integrity=None;actual=[]
    if batch.output_hash:
        path=directory(batch)/'tickets.pdf'
        integrity=path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==batch.output_hash
        if verify and integrity:
            try:
                with fitz.open(path) as document:
                    for page in document:
                        pix=page.get_pixmap(matrix=fitz.Matrix(4,4),alpha=False)
                        hashes=[hashlib.sha256(b.bytes).hexdigest() for b in decode(Image.frombytes('RGB',[pix.width,pix.height],pix.samples))]
                        values={}
                        for key,y in {'expiry':75.2,'package':82.6,'park_time':89.4,'show_time':93,'ticket_code':98,'agent':104.3}.items():
                            text=page.get_text('text',clip=fitz.Rect(24*72/25.4,(y-3.5)*72/25.4,79*72/25.4,(y+1)*72/25.4))
                            values[key]=re.sub(r'^(PARK|SHOW):\s*','',clean(text))
                        actual.append({'hashes':hashes,'fields':values})
            except Exception:integrity=False
    for index,selected in enumerate(batch.selected):
        original=originals.get(selected['page'],{});fields=[]
        for key in FIELDS:
            source=original.get(key,'');output=actual[index]['fields'][key] if verify and index<len(actual) else selected.get(key,'')
            fields.append({'key':key,'source':source,'output':output,'status':'missing' if not source or not output else 'match' if clean(source)==clean(output) else 'different'})
        qr=(actual[index]['hashes']==[original.get('qr_hash')] if verify and index<len(actual) else selected.get('qr_hash')==original.get('qr_hash'))
        details.append({'page':selected['page'],'sourceIndex':original.get('source_index',1),'sourcePage':original.get('source_page',selected['page']),'outputPage':index+1,'qrMatch':qr,'fields':fields})
    status='missing' if not batch.output_hash or not details else 'different' if not integrity or any(not d['qrMatch'] or any(f['status']=='different' for f in d['fields']) for d in details) else 'missing' if any(f['status']=='missing' for d in details for f in d['fields']) else 'match'
    if verify and batch.output_hash and len(actual)!=len(batch.selected):status='different'
    return {'status':status,'integrity':integrity,'verifiedPdf':verify and bool(batch.output_hash),'archived':bool(batch.superseded_at) or batch.booking_version!=booking.get('counterVersion',1),'quantityMatchesBooking':len(batch.selected)==int(booking.get('qty',0)),'details':details}

@login_required
@never_cache
def report_page(request):
    if not report_allowed(request.user):return render(request,'counter_report_denied.html',status=403)
    return render(request,'counter_report.html')

@login_required
@never_cache
@require_GET
def report_api(request):
    if not report_allowed(request.user):return JsonResponse({'error':'Chưa có quyền báo cáo đối chiếu vé.'},status=403)
    bookings=rows_for(request.user);query=request.GET;result=[]
    for booking in bookings:
        day=booking.get('date','')
        if query.get('from') and day<query['from'] or query.get('to') and day>query['to']:continue
        if query.get('seller') and query['seller'].casefold() not in booking.get('agent','').casefold():continue
        if query.get('q') and query['q'].casefold() not in booking.get('bookingCode','').casefold():continue
        batches=list(CounterTicketBatch.objects.filter(booking_id=booking['id']).order_by('-created_at'))
        for batch in batches or [None]:
            check=comparison(batch,booking) if batch else {'status':'missing','archived':False,'quantityMatchesBooking':False}
            if query.get('status') and query['status']!=check['status']:continue
            result.append({'bookingId':booking['id'],'code':booking.get('bookingCode'),'date':day,'seller':booking.get('agent'),'qty':booking['qty'],'batchId':str(batch.pk) if batch else None,'createdAt':batch.created_at.isoformat() if batch else '',**{k:check[k] for k in ('status','archived','quantityMatchesBooking')}})
    result.sort(key=lambda r:(r['date'],r['createdAt']),reverse=True)
    return JsonResponse({'rows':result[:200],'total':len(result),'note':'Danh sách so thông tin lưu và tính toàn vẹn file. Mở chi tiết để quét lại QR và đọc chữ trực tiếp từ PDF đầu ra.'})

@login_required
@never_cache
@require_GET
def report_detail(request,batch_id):
    batch,booking=report_batch(request.user,batch_id)
    return JsonResponse({'code':booking.get('bookingCode'),'seller':booking.get('agent'),'createdBy':batch.owner.get_username(),'createdAt':batch.created_at.isoformat(),'emailedAt':batch.emailed_at.isoformat() if batch.emailed_at else None,'batchId':str(batch.pk),**comparison(batch,booking,True)})

@login_required
@never_cache
@require_GET
@xframe_options_sameorigin
def report_file(request,batch_id):
    batch,_=report_batch(request.user,batch_id);folder=directory(batch)
    if request.GET.get('output')=='1':
        path=folder/'tickets.pdf'
        if not batch.output_hash or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=batch.output_hash:raise Http404()
        blob=path.read_bytes();name='output.pdf'
    else:
        try:index=int(request.GET.get('source','1'))
        except ValueError:raise Http404()
        if index not in {r.get('source_index',1) for r in batch.rows}:raise Http404()
        path=folder/('original-'+str(index))
        if not path.is_file():path=folder/'source'
        if not path.is_file():raise Http404()
        blob=path.read_bytes();name='source'
    mime='application/pdf' if blob.startswith(b'%PDF-') else 'image/png' if blob.startswith(b'\x89PNG') else 'image/jpeg' if blob.startswith(b'\xff\xd8') else 'application/zip'
    return FileResponse(BytesIO(blob),content_type=mime,as_attachment=mime=='application/zip',filename=name)
