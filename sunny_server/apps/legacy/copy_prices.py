import copy
import json
import uuid
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Workspace
from .operations import can, save_workspace
from .pricing import effective, row_ticket, sell_price, unique_price, amount, validate
from .ticket_lifecycle import enforce_ticket_lifecycle

def preview(data,params):
    source=next((a for a in data.get('agents',[]) if a['id']==params['source']),None)
    target=next((a for a in data.get('agents',[]) if a['id']==params['target']),None)
    if not source or not target or source['id']==target['id']: raise ValueError('Chọn hai đối tác nguồn và đích khác nhau.')
    if any(sum(a.get('name')==p['name'] for a in data.get('agents',[]))!=1 for p in (source,target)): raise ValueError('Tên đối tác bị trùng, cần đối soát trước khi sao chép giá.')
    source_date=params['sourceDate'];start=params['from'];end=params.get('to','')
    for d in (source_date,start,end):
        if d: date.fromisoformat(d)
    if not source_date or not start or end and end<start: raise ValueError('Ngày hiệu lực không hợp lệ.')
    mode=params.get('mode','private')
    if mode not in ('private','effective'): raise ValueError('Nguồn giá không hợp lệ.')
    selected=params.get('tickets')
    if selected is not None and (not isinstance(selected,list) or any(not isinstance(t,str) for t in selected)): raise ValueError('Danh sách loại vé không hợp lệ.')
    result=[]
    for ticket in data.get('ticketTypes',[]):
        if not ticket.get('active',True) or selected is not None and ticket['id'] not in selected: continue
        if mode=='effective':price,origin=sell_price(data,source['id'],ticket['id'],source_date)
        else:
            rows=[p for p in data.get('agentPrices',[]) if p.get('agent')==source['name'] and row_ticket(data,p)==ticket['id'] and effective(p,source_date)]
            price=unique_price(rows);origin='Giá riêng'
        if price is None: continue
        existing=[p for p in data.get('agentPrices',[]) if p.get('agent')==target['name'] and row_ticket(data,p)==ticket['id'] and (p.get('from') or '')<=(end or '9999-12-31') and start<=(p.get('to') or '9999-12-31')]
        duplicate=any(amount(p['price'])==amount(price) and (p.get('from') or '')<=start and (p.get('to') or '9999-12-31')>=(end or '9999-12-31') for p in existing)
        status='duplicate' if duplicate else 'conflict' if existing else 'add'
        result.append({'ticketId':ticket['id'],'ticketType':ticket['name'],'price':price,'origin':origin,'status':status,'from':start,'to':end})
    return source,target,result

@login_required
@require_http_methods(['POST'])
def copy_prices(request):
    user=request.user
    if not (user.is_superuser or user.role in ('admin','operator')): return JsonResponse({'error':'Không được phép.'},status=403)
    if not can(user,'agency.view') or not can(user,'agency_price.view'): return JsonResponse({'error':'Cần quyền xem đối tác và giá nguồn.'},status=403)
    try:
        params=json.loads(request.body)
        obj=Workspace.objects.get(pk=1)
        revision=int(params['revision'])
        if revision!=obj.revision: return JsonResponse({'error':'Dữ liệu đã đổi. Tải lại và xem trước lại.'},status=409)
        action=params.get('action','preview')
        if action not in ('preview','apply','assign'): raise ValueError('Thao tác không hợp lệ.')
        if params.get('mode')=='effective' and (not can(user,'price_list.view') or not can(user,'price_list_item.view')): return JsonResponse({'error':'Cần quyền xem bảng giá chung để sao chép giá kế thừa.'},status=403)
        source,target,rows=preview(obj.data,params)
        group=next((g for g in obj.data.get('priceLists',[]) if g['id']==source.get('priceListId') and g.get('active',True)),None)
        if action=='preview':return JsonResponse({'revision':revision,'rows':rows,'sourceName':source['name'],'targetName':target['name'],'sourcePriceList':{'id':group['id'],'name':group['name']} if group and can(user,'price_list.view') else None})
        data=copy.deepcopy(obj.data)
        if action=='assign':
            if not can(user,'agency.assign_price_list') or not can(user,'price_list.view'): return JsonResponse({'error':'Không có quyền gán bảng giá chung.'},status=403)
            if not group: raise ValueError('Nguồn không có bảng giá chung đang hoạt động.')
            for a in data['agents']:
                if a['id']==target['id']: a['priceListId']=group['id']
            added=0
        else:
            if not can(user,'agency_price.create'): return JsonResponse({'error':'Không có quyền thêm giá riêng cho đối tác đích.'},status=403)
            if not params.get('tickets'): raise ValueError('Chọn ít nhất một loại vé để sao chép.')
            additions=[dict(id=str(uuid.uuid4()),agent=target['name'],ticketId=r['ticketId'],ticketType=r['ticketType'],price=r['price'],**{'from':r['from'],'to':r['to']}) for r in rows if r['status']=='add']
            added=len(additions)
            if not added:return JsonResponse({'revision':revision,'added':0,'skipped':len(rows)})
            data.setdefault('agentPrices',[]).extend(additions)
        validate(data);enforce_ticket_lifecycle(obj.data,data)
        with transaction.atomic():save_workspace(obj,data,user,revision,'prices.copy' if action=='apply' else 'prices.assign_list')
        return JsonResponse({'revision':revision+1,'added':added,'skipped':len(rows)-added})
    except (ValueError,TypeError,KeyError,Workspace.DoesNotExist) as exc:return JsonResponse({'error':str(exc)},status=400)
    except RuntimeError as exc:return JsonResponse({'error':str(exc)},status=409)
