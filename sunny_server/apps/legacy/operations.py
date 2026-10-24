import copy
import json
import uuid
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.audit.models import AuditLog
from apps.agencies.models import Agency
from .models import Workspace
from .access import allowed, full_access, RESOURCES, NUMBERS, BOOLS, can_field, projected, action_permission
from .pricing import validate, amount, calculate_booking, sell_price, supplier_options, choose_cost
from .ticket_lifecycle import ticket_used, enforce_ticket_lifecycle

def can(user,name): return full_access(user) or allowed(user,name)

def save_workspace(obj,data,user,revision,action):
    if not Workspace.objects.filter(pk=obj.pk,revision=revision).update(data=data,revision=F('revision')+1):
        raise RuntimeError('Dữ liệu đã đổi; tải lại trước khi tiếp tục.')
    for a in data.get('agents',[]):
        Agency.objects.update_or_create(legacy_id=a['id'],defaults={'name':a['name']})
    AuditLog.objects.create(user=user,action=action[:100],revision=revision+1)

@login_required
@require_http_methods(['GET','POST'])
def operations(request):
    user=request.user
    if not (user.is_superuser or user.role in ('admin','operator')): return JsonResponse({'error':'Không được phép.'},status=403)
    obj,_=Workspace.objects.get_or_create(pk=1)
    if request.method=='GET':
        resources={}
        for key,(prefix,label,fields) in RESOURCES.items():
            if not can(user,prefix+'.view'): continue
            rows=[dict(projected(user,key,r),_index=i) for i,r in enumerate(obj.data.get(key,[]))]
            if key=='ticketTypes':
                for row in rows: row['_deletable']=not ticket_used(obj.data,row)
            readable=projected(user,key,{f:'' for f in fields})
            def permitted(action):
                if key=='cashTransactions': return any(can(user,action_permission(key,action,k)) for k in ('capital','income','expense'))
                return can(user,action_permission(key,action))
            resources[key]={'label':label,'fields':{k:v for k,v in fields.items() if k in readable},'editable':[f for f in fields if f in readable and can_field(user,key,f)],'rows':rows,'create':permitted('create'),'change':permitted('change'),'delete':permitted('delete')}
        lookups={}
        if resources:
            # Minimal names/IDs for foreign-key selectors; never send costs or contacts here.
            for key in ('ticketTypes','agents','suppliers','priceLists'):
                lookups[key]=[{'id':r['id'],'name':r.get('name','')} for r in obj.data.get(key,[]) if r.get('active',True)]
            if can(user,'booking.view_buy_price'):
                lookups['costPrices']=[{'id':p.get('id') or f'cost-row-{i}','name':str(p.get('ticketType') or p.get('ticketId'))+' / '+str(next((s['name'] for s in obj.data.get('suppliers',[]) if s['id']==p.get('supplierId')),p.get('supplierId','')))+' — '+str(p['price'])+(' (mặc định)' if p.get('isDefault') else '')} for i,p in enumerate(obj.data.get('costPrices',[]))]
        return JsonResponse({'revision':obj.revision,'resources':resources,'lookups':lookups,'payments':{'receipt':{p:can(user,'receipt.'+p) for p in ('view','create','change','delete')},'supplier':{p:can(user,'supplier_payment.'+p) for p in ('view','create','delete')}}})
    try:
        body=json.loads(request.body)
        revision=int(body['revision'])
        if revision!=obj.revision: raise RuntimeError('Dữ liệu đã đổi; tải lại.')
        data=copy.deepcopy(obj.data)
        action=body['action']
        if action=='payment':
            index=int(body['bookingIndex']); booking=data.get('bookings',[])[index]
            kind=body['kind']; op=body['operation']
            if kind not in ('receipt','supplier') or op not in ('create','change','delete'): raise ValueError('Thao tác không hợp lệ.')
            prefix='receipt' if kind=='receipt' else 'supplier_payment'
            if not can(user,'booking.view') or not can(user,prefix+'.view') or not can(user,prefix+'.'+op): return JsonResponse({'error':'Không có quyền thanh toán.'},status=403)
            key='payments' if kind=='receipt' else 'supplierPayments'
            payments=booking.setdefault(key,[])
            if op=='delete': payments.pop(int(body['index']))
            else:
                payment={k:body['values'].get(k,'') for k in ('date','amount','note')}
                if amount(payment['amount'])<=0 or not payment['date']: raise ValueError('Ngày và số tiền không hợp lệ.')
                payment['amount']=float(amount(payment['amount']))
                if op=='create': payments.append(payment)
                else: payments[int(body['index'])]=payment
            calculate_booking(booking)
        elif action in ('create','change','delete'):
            resource=body['resource']
            prefix,label,fields=RESOURCES[resource]
            rows=data.setdefault(resource,[])
            index=int(body.get('index',-1))
            if action!='create' and (index<0 or index>=len(rows)): raise ValueError('Không tìm thấy bản ghi.')
            old=copy.deepcopy(rows[index]) if action!='create' else {}
            kind=old.get('kind') if action!='create' else body.get('values',{}).get('kind')
            if not can(user,prefix+'.view') or not can(user,action_permission(resource,action,kind)): return JsonResponse({'error':'Không có quyền '+action+' '+label},status=403)
            if action=='delete':
                if resource=='bookings' and (old.get('payments') or old.get('supplierPayments')): raise ValueError('Không xóa booking đã có thanh toán ở màn hình phân quyền; cần quản trị đối soát.')
                if resource=='ticketTypes' and ticket_used(obj.data,old): raise ValueError('Loại vé đã phát sinh dữ liệu; chỉ được dừng sử dụng.')
                if resource in ('agents','suppliers','priceLists'): raise ValueError('Dùng ngừng hoạt động để giữ liên kết lịch sử; xóa danh mục cần quản trị dữ liệu.')
                rows.pop(index)
            else:
                values=body.get('values',{})
                if not isinstance(values,dict) or set(values)-set(fields): raise ValueError('Có trường không được phép.')
                row=copy.deepcopy(old)
                if resource=='cashTransactions' and action!='create' and values.get('kind',old.get('kind'))!=old.get('kind'): raise ValueError('Không đổi loại giao dịch vốn/thu/chi.')
                readable=projected(user,resource,{f:'' for f in fields})
                for f,v in values.items():
                    if f not in readable or not can_field(user,resource,f):
                        if v!=old.get(f): return JsonResponse({'error':'Không có quyền sửa trường '+f},status=403)
                        continue
                    if f in NUMBERS: v=float(amount(v or 0))
                    if f in BOOLS and not isinstance(v,bool): raise ValueError('Trạng thái không hợp lệ.')
                    row[f]=v
                if action=='create': row.setdefault('id',str(uuid.uuid4()))
                elif row.get('id')!=old.get('id'): raise ValueError('Không được đổi mã định danh.')
                if resource=='agents' and old and row.get('name')!=old.get('name'): raise ValueError('Đổi tên đại lý có lịch sử cần quản trị chuyển đổi liên kết.')
                if resource=='bookings':
                    if old.get('supplierPayments') and row.get('supplierId')!=old.get('supplierId'): raise ValueError('Không đổi nguồn booking đã có khoản chi.')
                    ticket=next((t for t in data.get('ticketTypes',[]) if t['id']==row.get('ticketId') and t.get('active',True)),None)
                    if not ticket: raise ValueError('Loại vé không hợp lệ.')
                    if action=='create' or row.get('ticketId')!=old.get('ticketId'): row['ticketType']=ticket['name']
                    needs_quote=action=='create' or any(row.get(f)!=old.get(f) for f in ('agent','ticketId','date','customerType','supplierId','costPriceId'))
                    if needs_quote:
                        if row.get('customerType')=='agent':
                            agency=next((a for a in data.get('agents',[]) if a['name']==row.get('agent') and a.get('active',True)),None)
                            if not agency: raise ValueError('Đại lý không hợp lệ.')
                            price,source=sell_price(data,agency['id'],row['ticketId'],row['date'])
                            if price is None: raise ValueError('Chưa có giá bán hợp lệ.')
                            if not can(user,'booking.change_sell_price') or 'sellPrice' not in values: row['sellPrice']=price
                            row['salePriceSource']=source
                        elif action=='create' and not can(user,'booking.change_sell_price'): raise ValueError('Khách lẻ cần quyền nhập giá bán.')
                        choice_id=values.get('costPriceId') if 'costPriceId' in values else (old.get('costPriceId') if all(row.get(f)==old.get(f) for f in ('supplierId','ticketId','date')) else None)
                        selected=choose_cost(data,row['ticketId'],row.get('supplierId'),row.get('date',''),choice_id)
                        if choice_id or not can(user,'booking.change_buy_price') or 'buyPrice' not in values: row['buyPrice']=selected['price']
                        row['supplierName']=selected['supplierName']
                        row['costPriceId']=selected['id']
                    row.setdefault('buyPrice',0);row.setdefault('sellPrice',0);row.setdefault('qty',1)
                    row.setdefault('cost',0);row.setdefault('payments',[]);row.setdefault('supplierPayments',[])
                    row.setdefault('bookingCode','ST-'+str(uuid.uuid4())[:12].upper())
                    calculate_booking(row)
                if resource=='zaloCampaigns' and action=='create': row.update(recipients=[],media=[],createdAt=__import__('datetime').date.today().isoformat())
                if resource=='cashTransactions' and (not row.get('date') or amount(row.get('amount',0))<=0): raise ValueError('Nhập ngày và số tiền dương.')
                if resource=='costPrices' and row.get('isDefault'):
                    for p in rows:
                        if p.get('ticketId')==row.get('ticketId') and p.get('supplierId')==row.get('supplierId'): p['isDefault']=False
                if action=='create': rows.append(row)
                else: rows[index]=row
        else: raise ValueError('Thao tác không hỗ trợ.')
        validate(data)
        enforce_ticket_lifecycle(obj.data,data)
        with transaction.atomic(): save_workspace(obj,data,user,revision,'operation.'+action)
        return JsonResponse({'revision':revision+1})
    except RuntimeError as e: return JsonResponse({'error':str(e)},status=409)
    except (ValueError,KeyError,TypeError,IndexError) as e: return JsonResponse({'error':str(e) or 'Dữ liệu không hợp lệ'},status=400)

@login_required
@require_http_methods(['GET'])
def quote(request):
    if not (request.user.is_superuser or request.user.role in ('admin','operator')) or not can(request.user,'booking.create'): return JsonResponse({'error':'Không có quyền tạo booking'},status=403)
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    try:
        price,source=sell_price(data,request.GET['agency'],request.GET['ticket'],request.GET['date'])
        options=supplier_options(data,request.GET['ticket'],request.GET['date'])
        if not can(request.user,'booking.view_buy_price'): options=[{'supplierId':p['supplierId'],'supplierName':p['supplierName']} for p in options]
        return JsonResponse({'price':price,'source':source,'options':options})
    except (ValueError,KeyError) as e: return JsonResponse({'error':str(e)},status=400)
