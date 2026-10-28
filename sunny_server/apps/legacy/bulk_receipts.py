import copy
import hashlib
import json
import uuid
from datetime import date
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .models import Workspace
from .operations import can, save_workspace
from .pricing import amount

def party_for(booking, data):
    if booking.get('customerType') != 'agent':
        # No dependable shared identity exists for retail customers in legacy data.
        return 'booking:'+str(booking.get('id')), (booking.get('customerName') or booking.get('agent') or 'Khách lẻ')+' — riêng booking '+str(booking.get('bookingCode') or booking.get('id'))
    agents=data.get('agents',[])
    matches=[a for a in agents if a.get('id')==booking.get('agentId')] if booking.get('agentId') else [a for a in agents if a.get('name')==booking.get('agent')]
    if len(matches)!=1: return None,None
    return 'agent:'+str(matches[0]['id']),str(matches[0]['name'])+' ('+str(matches[0]['id'])+')'

def balance(booking):
    return max(Decimal('0'),amount(booking.get('revenue',0))-sum((amount(p.get('amount',0)) for p in booking.get('payments',[])),Decimal('0')))

def receipt_row(b):
    return {'id':b['id'],'code':b.get('bookingCode') or b['id'],'date':b.get('date',''),'ticket':b.get('ticketType',''),'due':float(balance(b))}

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def bulk_receipts(request):
    return process_bulk(request)

def process_bulk(request, supplier=False):
    get_balance=supplier_balance if supplier else balance
    resolve_party=supplier_party_for if supplier else party_for
    payments_key='supplierPayments' if supplier else 'payments'
    batches_key='supplierPaymentBatches' if supplier else 'receiptBatches'
    prefix='supplier_payment' if supplier else 'receipt'
    def row_for(b): return {'id':b['id'],'code':b.get('bookingCode') or b['id'],'date':b.get('date',''),'ticket':b.get('ticketType',''),'due':float(get_balance(b))}
    user=request.user
    if not (user.is_superuser or user.role in ('admin','operator')) or not all(can(user,p) for p in ('booking.view',prefix+'.view',prefix+'.create')+ (('booking.view_buy_price',) if supplier else ())):
        return JsonResponse({'error':'Cần quyền xem booking, xem/tạo khoản thanh toán; phía nhà cung cấp cần quyền xem giá vốn.'},status=403)
    obj,_=Workspace.objects.get_or_create(pk=1)
    try:
        if request.method=='GET':
            parties={};unresolved=0
            for b in obj.data.get('bookings',[]):
                if not b.get('id') or get_balance(b)<=0: continue
                key,label=resolve_party(b,obj.data)
                if not key: unresolved+=1;continue
                parties.setdefault(key,{'id':key,'name':label,'rows':[]})['rows'].append(row_for(b))
            return JsonResponse({'revision':obj.revision,'parties':list(parties.values()),'unresolved':unresolved})
        body=json.loads(request.body);action=body.get('action')
        if action not in ('preview','apply'): raise ValueError('Thao tác không hợp lệ.')
        ids=body.get('ids');party=body.get('party');day=body.get('date');note=body.get('note','')
        if not isinstance(ids,list) or not ids or len(ids)>2000 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids): raise ValueError('Chọn booking hợp lệ, không trùng (tối đa 2000 dòng).')
        if not isinstance(party,str) or not isinstance(note,str) or len(note)>2000: raise ValueError('Khách hàng hoặc ghi chú không hợp lệ.')
        if date.fromisoformat(day).isoformat()!=day: raise ValueError('Ngày thanh toán phải có định dạng YYYY-MM-DD.')
        batch_id=str(uuid.UUID(body['batchId'])) if action=='apply' else None
        fingerprint=hashlib.sha256(json.dumps({'ids':sorted(ids),'party':party,'date':day,'note':note},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if batch_id:
            previous=next((b for b in obj.data.get(batches_key,[]) if b.get('id')==batch_id),None)
            if previous:
                if previous.get('fingerprint')!=fingerprint: raise ValueError('Mã đợt thanh toán đã dùng cho nội dung khác.')
                return JsonResponse({'revision':obj.revision,'batchId':batch_id,'total':previous['total'],'count':len(previous['bookingIds']),'duplicate':True})
        revision=body['revision']
        if not isinstance(revision,int) or revision!=obj.revision: return JsonResponse({'error':'Dữ liệu đã thay đổi. Đóng và mở lại màn hình thanh toán hàng loạt để kiểm tra số dư.'},status=409)
        data=copy.deepcopy(obj.data);by_id={}
        for b in data.get('bookings',[]): by_id.setdefault(str(b.get('id')),[]).append(b)
        selected=[]
        for key in ids:
            matches=by_id.get(key,[])
            if len(matches)!=1: raise ValueError('Booking không tồn tại hoặc mã định danh bị trùng.')
            b=matches[0]
            if resolve_party(b,data)[0]!=party: raise ValueError('Chỉ thanh toán booking của cùng một bên đã xác định.')
            if get_balance(b)<=0: raise ValueError('Booking đã tất toán. Hãy tải lại danh sách.')
            selected.append(b)
        rows=[row_for(b) for b in selected];total=sum((get_balance(b) for b in selected),Decimal('0'))
        if action=='preview': return JsonResponse({'revision':revision,'rows':rows,'total':float(total)})
        for b in selected:
            b.setdefault(payments_key,[]).append({'id':str(uuid.uuid4()),'batchId':batch_id,'date':day,'amount':float(get_balance(b)),'note':note})
        data.setdefault(batches_key,[]).append({'id':batch_id,'fingerprint':fingerprint,'party':party,'bookingIds':ids,'date':day,'note':note,'total':float(total),'createdBy':user.pk})
        with transaction.atomic(): save_workspace(obj,data,user,revision,prefix+'.bulk_create')
        return JsonResponse({'revision':revision+1,'batchId':batch_id,'total':float(total),'count':len(selected),'duplicate':False})
    except RuntimeError as exc: return JsonResponse({'error':str(exc)},status=409)
    except (ValueError,TypeError,KeyError) as exc: return JsonResponse({'error':str(exc) or 'Dữ liệu không hợp lệ.'},status=400)

def supplier_party_for(booking,data):
    if booking.get('costSource')=='manual' or booking.get('supplierId')=='__manual__':
        return 'booking:'+str(booking.get('id')), (booking.get('supplierName') or 'Nguồn nhập tay')+' — riêng booking '+str(booking.get('bookingCode') or booking.get('id'))
    matches=[s for s in data.get('suppliers',[]) if s.get('id')==booking.get('supplierId')]
    if len(matches)!=1: return None,None
    return 'supplier:'+str(matches[0]['id']),str(matches[0]['name'])+' ('+str(matches[0]['id'])+')'

def supplier_balance(booking):
    return max(Decimal('0'),amount(booking.get('buyPrice',0))*amount(booking.get('qty',0))-sum((amount(p.get('amount',0)) for p in booking.get('supplierPayments',[])),Decimal('0')))

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def bulk_supplier_payments(request):
    return process_bulk(request,supplier=True)