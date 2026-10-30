import copy
import json
import re
from django.contrib.auth.decorators import login_required
from django.db import transaction, OperationalError
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .access import full_access
from .counter import permitted, PAYMENT_METHODS
from .models import Workspace
from .operations import save_workspace
from .pricing import amount

TOKENS={'ma_booking':'Mã booking','loai_ve':'Loại vé','so_luong':'Số lượng vé','tong_tien':'Tổng tiền','ngay_booking':'Ngày booking','nguoi_ban':'Nhân viên bán vé','email_khach':'Email người nhận','phuong_thuc_thanh_toan':'Phương thức thanh toán'}
DEFAULT={'subject':'Vé {{ma_booking}} - Sunny Travel','body':'Kính gửi Quý khách,\n\nSunny Travel gửi vé của Quý khách trong file PDF đính kèm.\n\nMã booking: {{ma_booking}}\nLoại vé: {{loai_ve}}\nSố lượng: {{so_luong}}\nTổng tiền: {{tong_tien}}\n\nVui lòng kiểm tra thông tin và hạn sử dụng trên vé trước khi đến.\n\nTrân trọng,\nSunny Travel'}
PATTERN=re.compile(r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}')

def can_manage_template(user):return user.is_active and (user.is_superuser or user.role in ('admin','operator') and full_access(user))

def template_data(data):
    stored=data.get('settings',{}).get('counterEmailTemplate')
    return {key:stored[key] for key in ('subject','body')} if isinstance(stored,dict) and isinstance(stored.get('subject'),str) and isinstance(stored.get('body'),str) else dict(DEFAULT)

def checked_message(subject,body,template=False):
    if not isinstance(subject,str) or not isinstance(body,str):raise ValueError('Tiêu đề/nội dung phải là văn bản.')
    subject=subject.strip();body=body.strip()
    if not subject or len(subject)>200 or any(ord(c)<32 for c in subject):raise ValueError('Tiêu đề cần 1–200 ký tự, không xuống dòng.')
    if not body or len(body)>10000 or any(ord(c)<32 and c not in '\n\r\t' for c in body):raise ValueError('Nội dung cần 1–10000 ký tự.')
    if template:
        for value in (subject,body):
            if any(token not in TOKENS for token in PATTERN.findall(value)):raise ValueError('Có ô thay thế không được hỗ trợ. Chọn các ô trong danh sách.')
            remaining=PATTERN.sub('',value)
            if '{{' in remaining or '}}' in remaining:raise ValueError('Ô thay thế cần đúng dạng {{ma_booking}}.')
    return {'subject':subject,'body':body}

def render_email(booking,recipient='',data=None):
    if data is None:data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    template=checked_message(**template_data(data),template=True)
    values={'ma_booking':str(booking.get('bookingCode','')),'loai_ve':str(booking.get('ticketType','')),'so_luong':str(booking.get('qty','')),'tong_tien':f"{amount(booking.get('revenue',0)):,.0f}".replace(',','.')+' đ','ngay_booking':str(booking.get('date','')),'nguoi_ban':str(booking.get('agent','')),'email_khach':str(recipient or booking.get('customerEmail',''))}
    values['phuong_thuc_thanh_toan']=PAYMENT_METHODS.get(booking.get('paymentMethod'),'Chưa ghi nhận')
    # String substitution only, no template code or HTML evaluation.
    return checked_message(**{key:PATTERN.sub(lambda match:values[match.group(1)],value) for key,value in template.items()})

def readable(user):return can_manage_template(user) or permitted(user,'view')

@login_required
@never_cache
@ensure_csrf_cookie
def email_template_page(request):
    if not readable(request.user):return HttpResponseForbidden('Chưa có quyền xem mẫu email gửi vé.')
    return render(request,'counter_email_template.html',{'report_visible':permitted(request.user,'view') and permitted(request.user,'report')})

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def email_template_api(request):
    if not readable(request.user) or request.method=='POST' and not can_manage_template(request.user):return JsonResponse({'error':'Chỉ quản trị có quyền toàn bộ workspace được sửa mẫu email dùng chung.'},status=403)
    obj,_=Workspace.objects.get_or_create(pk=1)
    if request.method=='GET':return JsonResponse({'revision':obj.revision,'template':template_data(obj.data),'tokens':TOKENS,'canManage':can_manage_template(request.user)})
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict) or set(body)-{'revision','subject','body'}:raise ValueError('Dữ liệu không hợp lệ.')
        if type(body.get('revision')) is not int or body['revision']!=obj.revision:raise RuntimeError('Mẫu hoặc dữ liệu đã đổi. Tải lại trước khi lưu.')
        template=checked_message(body.get('subject'),body.get('body'),template=True)
        data=copy.deepcopy(obj.data);data.setdefault('settings',{})['counterEmailTemplate']=template
        with transaction.atomic():save_workspace(obj,data,request.user,obj.revision,'counter.email_template_change')
        return JsonResponse({'revision':obj.revision+1,'template':template})
    except (RuntimeError,OperationalError):return JsonResponse({'error':'Dữ liệu vừa thay đổi. Bấm Tải lại mẫu trước khi lưu để không ghi đè.'},status=409)
    except (ValueError,KeyError,TypeError) as exc:return JsonResponse({'error':str(exc) or 'Mẫu chưa hợp lệ.'},status=400)
