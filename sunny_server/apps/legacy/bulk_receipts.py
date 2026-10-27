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
    user=request.user
    if not (user.is_superuser or user.role in ('admin','operator')) or not all(can(user,p) for p in ('booking.view','receipt.view','receipt.create')):
        return JsonResponse({'error':'Cần quyền xem booking, xem và tạo khoản thu.'},status=403)
    obj,_=Workspace.objects.get_or_create(pk=1)
    try:
        if request.method=='GET':
            parties={};unresolved=0
            for b in obj.data.get('bookings',[]):
                if not b.get('id') or balance(b)<=0: continue
                key,label=party_for(b,obj.data)
                if not key: unresolved+=1;continue
                parties.setdefault(key,{'id':key,'name':label,'rows':[]})['rows'].append(receipt_row(b))
            return JsonResponse({'revision':obj.revision,'parties':list(parties.values()),'unresolved':unresolved})
        body=json.loads(request.body);action=body.get('action')
        if action not in ('preview','apply'): raise ValueError('Thao tác không hợp lệ.')
        ids=body.get('ids');party=body.get('party');day=body.get('date');note=body.get('note','')
        if not isinstance(ids,list) or not ids or len(ids)>2000 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids): raise ValueError('Chọn booking hợp lệ, không trùng (tối đa 2000 dòng).')
        if not isinstance(party,str) or not isinstance(note,str) or len(note)>2000: raise ValueError('Khách hàng hoặc ghi chú không hợp lệ.')
        if date.fromisoformat(day).isoformat()!=day: raise ValueError('Ngày thu phải có định dạng YYYY-MM-DD.')
        batch_id=str(uuid.UUID(body['batchId'])) if action=='apply' else None
        fingerprint=hashlib.sha256(json.dumps({'ids':sorted(ids),'party':party,'date':day,'note':note},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if batch_id:
            previous=next((b for b in obj.data.get('receiptBatches',[]) if b.get('id')==batch_id),None)
            if previous:
                if previous.get('fingerprint')!=fingerprint: raise ValueError('Mã đợt thu đã dùng cho nội dung khác.')
                return JsonResponse({'revision':obj.revision,'batchId':batch_id,'total':previous['total'],'count':len(previous['bookingIds']),'duplicate':True})
        revision=body['revision']
        if not isinstance(revision,int) or revision!=obj.revision: return JsonResponse({'error':'Dữ liệu đã thay đổi. Đóng và mở lại Thu tiền hàng loạt để kiểm tra số dư.'},status=409)
        data=copy.deepcopy(obj.data);by_id={}
        for b in data.get('bookings',[]): by_id.setdefault(str(b.get('id')),[]).append(b)
        selected=[]
        for key in ids:
            matches=by_id.get(key,[])
            if len(matches)!=1: raise ValueError('Booking không tồn tại hoặc mã định danh bị trùng.')
            b=matches[0]
            if party_for(b,data)[0]!=party: raise ValueError('Chỉ thu các booking của cùng một đối tác/khách hàng đã xác định.')
            if balance(b)<=0: raise ValueError('Booking đã tất toán. Hãy tải lại danh sách.')
            selected.append(b)
        rows=[receipt_row(b) for b in selected];total=sum((balance(b) for b in selected),Decimal('0'))
        if action=='preview': return JsonResponse({'revision':revision,'rows':rows,'total':float(total)})
        for b in selected:
            b.setdefault('payments',[]).append({'id':str(uuid.uuid4()),'batchId':batch_id,'date':day,'amount':float(balance(b)),'note':note})
        data.setdefault('receiptBatches',[]).append({'id':batch_id,'fingerprint':fingerprint,'party':party,'bookingIds':ids,'date':day,'note':note,'total':float(total),'createdBy':user.pk})
        with transaction.atomic(): save_workspace(obj,data,user,revision,'receipt.bulk_create')
        return JsonResponse({'revision':revision+1,'batchId':batch_id,'total':float(total),'count':len(selected),'duplicate':False})
    except RuntimeError as exc: return JsonResponse({'error':str(exc)},status=409)
    except (ValueError,TypeError,KeyError) as exc: return JsonResponse({'error':str(exc) or 'Dữ liệu không hợp lệ.'},status=400)
