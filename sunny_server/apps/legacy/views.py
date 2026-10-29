import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from apps.agencies.models import Agency
from apps.audit.models import AuditLog
from .models import Workspace, Attachment
from .access import full_access, allowed
from .pricing import validate, prepare_manual_cost, calculate_booking
from .ticket_lifecycle import enforce_ticket_lifecycle
from .partners import enforce_partner_types
from django.views.decorators.cache import never_cache

def internal(user):
    return user.is_superuser or user.role in ('admin','operator')

@login_required
@ensure_csrf_cookie
def home(request):
    if request.user.role=='counter': return redirect('counter-page')
    if internal(request.user):
        return render(request, 'legacy.html' if full_access(request.user) else 'restricted.html')
    data = Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    agency = request.user.agency
    # Legacy records refer to agency names: deny ambiguous names rather than leak data.
    valid = agency and sum(a.get('name') == agency.name for a in data.get('agents',[])) == 1 and any(str(a.get('id')) == agency.legacy_id and a.get('name') == agency.name for a in data.get('agents',[]))
    bookings = []
    if valid:
        for b in data.get('bookings',[]):
            if b.get('customerType') == 'agent' and b.get('agent') == agency.name:
                paid = sum(float(p.get('amount',0)) for p in b.get('payments',[]))
                bookings.append({'code':b.get('bookingCode'), 'date':b.get('date'), 'ticket':b.get('ticketType'), 'qty':b.get('qty'), 'total':b.get('revenue'), 'paid':paid, 'due':max(0,float(b.get('revenue',0))-paid)})
    return render(request,'agency.html',{'agency':agency,'bookings':bookings})

@login_required
@never_cache
@require_http_methods(['GET','PUT'])
def state(request):
    if not internal(request.user) or not full_access(request.user): return JsonResponse({'error':'Cần quyền toàn bộ workspace để dùng API dữ liệu đầy đủ.'},status=403)
    obj, _ = Workspace.objects.get_or_create(pk=1)
    if request.method == 'GET': return JsonResponse({'data':obj.data,'revision':obj.revision})
    try:
        payload = json.loads(request.body)
        data, revision = payload['data'], int(payload['revision'])
        if not isinstance(data,dict): raise ValueError()
        validate(data)
        previous={b.get('id'):b for b in obj.data.get('bookings',[])}
        for b in data.get('bookings',[]):
            if b.get('costSource')=='manual' and b!=previous.get(b.get('id')):
                prepare_manual_cost(b);calculate_booking(b)
        enforce_ticket_lifecycle(obj.data,data)
        enforce_partner_types(obj.data,data)
        old_bookings={b.get('id'):b for b in obj.data.get('bookings',[])}
        for booking in data.get('bookings',[]):
            old=old_bookings.get(booking.get('id'))
            if old and old.get('supplierPayments') and (booking.get('supplierId')!=old.get('supplierId') or old.get('costSource')=='manual' and booking.get('supplierName')!=old.get('supplierName')):
                raise ValueError('Không đổi nhà cung cấp của booking đã có khoản chi. Cần đối soát trước.')
        for key in ['agents','ticketTypes','bookings','agentPrices','costPrices','expenses','cashTransactions','zaloCampaigns']:
            if key in data and (not isinstance(data[key],list) or any(not isinstance(x,dict) for x in data[key])): raise ValueError()
        agents = data.get('agents',[])
        ids = [str(a['id']) for a in agents]
        if len(ids) != len(set(ids)): raise ValueError()
    except (ValueError,KeyError,TypeError) as exc: return JsonResponse({'error':str(exc) or 'Dữ liệu không hợp lệ'},status=400)
    with transaction.atomic():
        updated = Workspace.objects.filter(pk=1,revision=revision).update(data=data,revision=F('revision')+1)
        if not updated: return JsonResponse({'error':'Người khác đã thay đổi dữ liệu. Tải lại trang trước khi sửa tiếp.'},status=409)
        for a in agents:
            Agency.objects.update_or_create(legacy_id=str(a['id']),defaults={'name':str(a.get('name',''))})
        AuditLog.objects.create(user=request.user,action='workspace.save',revision=revision+1)
    return JsonResponse({'revision':revision+1,'data':data})

@login_required
@require_http_methods(['GET','POST','DELETE'])
def media(request, key):
    if not internal(request.user) or not full_access(request.user): return HttpResponseForbidden()
    if request.method == 'POST':
        f = request.FILES.get('file')
        if not f or f.size > 20*1024*1024 or not f.content_type.startswith(('image/','video/')):
            return JsonResponse({'error':'Chỉ nhận ảnh/video tối đa 20 MB'},status=400)
        if Attachment.objects.filter(key=key).exists(): return JsonResponse({'error':'Trùng mã tệp'},status=409)
        Attachment.objects.create(key=key,file=f,name=f.name,content_type=f.content_type)
        return JsonResponse({'ok':True})
    obj = get_object_or_404(Attachment,key=key)
    if request.method == 'DELETE':
        obj.file.delete(); obj.delete()
        return JsonResponse({'ok':True})
    response = FileResponse(obj.file.open('rb'),as_attachment=True,filename=obj.name,content_type='application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    return response
