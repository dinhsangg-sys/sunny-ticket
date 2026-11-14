"""Read-only receipt report: classify each payment, never assume a booking's current method."""
import csv,re
from datetime import date
from decimal import Decimal
from io import StringIO
from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponse,HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .access import allowed,full_access
from .models import Workspace
from .pricing import amount

METHODS={'cash':'Tiền mặt','bank_transfer':'Chuyển khoản','card':'Thẻ thanh toán','unknown':'Chưa xác định'}
SOURCES={'tickets':'Bán vé / Booking','souvenirs':'Souvenirs'}
ZONE=ZoneInfo('Asia/Ho_Chi_Minh')

def permitted(user,source):
    if not user.is_authenticated or not user.is_active:return False
    if source=='tickets':return user.is_superuser or user.role in ('admin','operator') and (full_access(user) or allowed(user,'receipt.view') and allowed(user,'booking.view'))
    if source=='souvenirs' and settings.SOUVENIRS_ENABLED:
        from apps.souvenirs.views import can
        return can(user,'view_reports')
    return False

def day_of(value):
    if not isinstance(value,str):return ''
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        try:return date.fromisoformat(value).isoformat()
        except ValueError:return ''
    try:
        stamp=parse_datetime(value)
        return stamp.astimezone(ZONE).date().isoformat() if stamp and timezone.is_aware(stamp) else ''
    except (ValueError,TypeError,OverflowError):return ''

def payment_method(payment):
    value=payment.get('method') or payment.get('paymentMethod')
    if isinstance(value,str) and value in METHODS and value!='unknown':return value
    if isinstance(payment.get('cardFee'),dict) and 'feeAmount' in payment['cardFee']:return 'card'
    if payment.get('provider') in ('sepay','sepay_test'):return 'bank_transfer'
    return 'unknown'

def source_rows(source):
    if source=='tickets':
        data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
        for booking in data.get('bookings',[]):
            if booking.get('status') in ('cancelled','canceled') or booking.get('cancelledAt'):continue
            for index,payment in enumerate(booking.get('payments') or []):
                yield {'orderId':str(booking.get('id','')),'receiptId':str(payment.get('id') or index),'code':booking.get('bookingCode') or booking.get('id',''),'party':booking.get('customerName') or booking.get('agent') or 'Khách lẻ','date':day_of(payment.get('date')) or day_of(payment.get('createdAt')),'method':payment_method(payment),'amount':payment.get('amount',0),'feeData':payment.get('cardFee') or {}}
    else:
        from apps.souvenirs.models import SaleOrder
        for order in SaleOrder.objects.filter(status='paid',deleted_at__isnull=True).iterator():
            method=payment_method({'method':order.payment_method,'cardFee':order.card_fee})
            yield {'orderId':str(order.pk),'receiptId':str(order.pk),'code':order.code,'party':order.seller_name,'date':timezone.localtime(order.paid_at,ZONE).date().isoformat() if order.paid_at else '','method':method,'amount':order.total,'feeData':order.card_fee or {}}

def build_report(source,start,end,method):
    rows=[];warnings={'undatedCount':0,'undatedAmount':0,'invalidCount':0,'cardFeeMissingCount':0}
    for raw in source_rows(source):
        if method and raw['method']!=method:continue
        try:
            value=amount(raw['amount'])
            if not value:continue
            fee=amount(raw['feeData'].get('feeAmount',0))
            if fee>value:raise ValueError('Invalid fee')
        except (ValueError,AttributeError,TypeError):warnings['invalidCount']+=1;continue
        day=raw['date']
        if not day:
            warnings['undatedCount']+=1;warnings['undatedAmount']+=float(value)
            if start or end:continue
        elif (start and day<start) or (end and day>end):continue
        fee_known=raw['method']!='card' or 'feeAmount' in raw['feeData']
        if not fee_known:warnings['cardFeeMissingCount']+=1
        rows.append({k:raw[k] for k in ('orderId','receiptId','code','party','date','method')}|{'methodLabel':METHODS[raw['method']],'amount':float(value),'fee':float(fee),'net':float(value-fee),'feeKnown':fee_known})
    rows.sort(key=lambda r:(r['date'],r['code'],r['receiptId']),reverse=True)
    def totals(selected):
        return {'receipts':len(selected),'orders':len({r['orderId'] for r in selected}),**{k:float(sum((Decimal(str(r[k])) for r in selected),Decimal(0))) for k in ('amount','fee','net')}}
    groups=[{'method':key,'label':label,**totals([r for r in rows if r['method']==key])} for key,label in METHODS.items()]
    return {'source':source,'sourceLabel':SOURCES[source],'from':start,'to':end,'method':method,'groups':groups,'totals':totals(rows),'rows':rows,'warnings':warnings,'today':timezone.localdate().isoformat()}

def csv_response(data):
    stream=StringIO(newline='');writer=csv.writer(stream)
    def safe(value):
        if isinstance(value,str) and (value.lstrip().startswith(('=','+','-','@')) or value.startswith(('\t','\r','\n'))):return "'"+value
        return value
    writer.writerow(['SUNNY — THU TIỀN THEO PHƯƠNG THỨC',data['sourceLabel']]);writer.writerow(['Từ ngày',data['from'],'Đến ngày',data['to'],'Phương thức',METHODS.get(data['method'],'Tất cả')])
    writer.writerow(['Phương thức','Số khoản thu','Số booking/đơn','Tổng thu','Phí đã lưu','Thực nhận theo phí đã lưu'])
    for group in data['groups']:writer.writerow([group['label'],group['receipts'],group['orders'],group['amount'],group['fee'],group['net']])
    t=data['totals'];writer.writerow(['Tổng cộng',t['receipts'],t['orders'],t['amount'],t['fee'],t['net']]);writer.writerow([])
    writer.writerow(['Ngày thu','Mã booking/đơn','Khách hàng / Người bán','Phương thức','Tiền thu','Phí đã lưu','Thực nhận theo phí đã lưu','Ghi chú phí'])
    for r in data['rows']:writer.writerow([safe(r['date'] or 'Chưa xác định ngày'),safe(r['code']),safe(r['party']),r['methodLabel'],r['amount'],r['fee'],r['net'],'Chưa lưu phí thẻ' if not r['feeKnown'] else ''])
    writer.writerow([]);writer.writerow(['Khoản thiếu ngày (không được tính khi lọc ngày)',data['warnings']['undatedCount'],data['warnings']['undatedAmount']]);writer.writerow(['Khoản thẻ chưa lưu phí',data['warnings']['cardFeeMissingCount']]);writer.writerow(['Bản ghi không hợp lệ đã bỏ qua',data['warnings']['invalidCount']])
    response=HttpResponse('\ufeff'+stream.getvalue(),content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="Sunny-thu-tien-'+data['source']+'-'+(data['from'] or 'all')+'-'+(data['to'] or 'all')+'.csv"';return response

@login_required
@never_cache
@require_GET
def report_api(request):
    source=request.GET.get('source','tickets')
    if source not in SOURCES:return JsonResponse({'error':'Nguồn báo cáo không hợp lệ.'},status=400)
    if not permitted(request.user,source):return JsonResponse({'error':'Chưa có quyền xem báo cáo thu tiền của module này.'},status=403)
    try:
        start=request.GET.get('from','');end=request.GET.get('to','');method=request.GET.get('method','')
        for value in (start,end):
            if value and (not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value) or not day_of(value)):raise ValueError('Ngày cần đúng định dạng YYYY-MM-DD.')
        if start and end and start>end:raise ValueError('Từ ngày không thể sau Đến ngày.')
        if method and method not in METHODS:raise ValueError('Phương thức thanh toán không hợp lệ.')
        data=build_report(source,start,end,method)
        return csv_response(data) if request.GET.get('format')=='csv' else JsonResponse(data)
    except (ValueError,TypeError) as exc:return JsonResponse({'error':str(exc)},status=400)

@login_required
@never_cache
@require_GET
def report_page(request):
    source=request.GET.get('source','tickets')
    if not permitted(request.user,source):return HttpResponseForbidden('Chưa có quyền xem báo cáo thu tiền của module này.')
    return render(request,'payment_methods.html',{'source':source,'source_label':SOURCES[source],'back_url':'/souvenirs/manage/' if source=='souvenirs' else '/?view=reports#reports'})
