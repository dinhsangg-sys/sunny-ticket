import copy
from urllib.parse import urlencode
from django.utils.cache import patch_vary_headers
from django.utils.translation.trans_real import parse_accept_lang_header
from django.shortcuts import render

def language(request):
    selected=request.GET.get('lang')
    if selected in ('vi','en'):return selected
    for name in ('souvenirs_lang','sunny_lang'):
        if request.COOKIES.get(name) in ('vi','en'):return request.COOKIES[name]
    preferences=parse_accept_lang_header(request.headers.get('Accept-Language',''))
    preferred=next((code.lower().split('-')[0] for code,quality in preferences if quality>0),None)
    return 'vi' if preferred=='vi' else 'en'

def localized(obj,lang):
    result=copy.copy(obj)
    if lang=='en':
        for field in ('title','summary','body'):setattr(result,field,getattr(obj,field+'_en','') or getattr(obj,field))
    return result

MESSAGES={
 'Những trải nghiệm ở Hội An':'Experiences in Hoi An',
 'Chuyện kể từ Hội An':'Stories from Hoi An',
 'Đơn đang được hỗ trợ / đối soát':'Your order is being reviewed by our team',
 'Booking cần được đối soát':'Your booking needs to be reviewed by our team',
 'Đã gửi vé qua email':'Tickets sent by email',
 'Đã thanh toán — Chờ gửi vé':'Payment received — Tickets will be emailed',
 'QR đã hết hạn — chưa xác nhận thanh toán':'QR expired — Payment not confirmed',
 'Phiên thanh toán không khả dụng':'This payment session is unavailable',
 'Chờ thanh toán':'Awaiting payment',
 'Thanh toán online đang tạm đóng. Vui lòng quay lại sau.':'Online payments are temporarily unavailable. Please try again later.',
 'Lần đặt vé này đã dùng. Vui lòng mở lại biểu mẫu.':'This booking request has already been used. Please open a new booking form.',
 'Bạn đã gửi nhiều yêu cầu. Vui lòng thử lại sau.':'Too many requests. Please try again later.',
 'Yêu cầu đang được xử lý. Thử lại cùng biểu mẫu để tránh trùng đơn.':'Your request is being processed. Retry the same form to avoid a duplicate order.',
 'Loại vé đang tạm ngừng bán online.':'This ticket is not currently available online.',
 'Ngày đã chọn chưa có giá online duy nhất. Vui lòng chọn ngày khác hoặc liên hệ Sunny.':'No online price is available for this date. Please choose another date or contact Sunny.',
 'Giá online chưa hợp lệ.':'The online price is currently unavailable.',
 'Loại vé chưa có giá vốn mặc định hợp lệ. Liên hệ quản trị.':'This ticket is not ready for online booking. Please contact Sunny.',
 'Loại vé có nhiều giá vốn mặc định cùng ưu tiên. Liên hệ quản trị xác định lại.':'This ticket is not ready for online booking. Please contact Sunny.',
 'Đơn đã được xử lý.':'This order has already been processed.',
 'Thanh toán đang tạm đóng. Không chuyển tiền khi chưa có QR hợp lệ.':'Payments are temporarily unavailable. Do not transfer money without a valid QR code.',
 'Đơn đã quá thời hạn giữ giá 30 phút. Đặt lại để kiểm tra giá mới; không chuyển tiền theo đơn cũ.':'The 30-minute price hold has expired. Start a new booking to check the current price; do not pay this old order.',
 'Đơn đang được cập nhật. Tải lại trang trước khi thử lại.':'This order is being updated. Reload the page before trying again.',
}
def text(value,lang):return MESSAGES.get(str(value),str(value)) if lang=='en' else value

def public_render(request,template,context):
    lang=language(request)
    def url(value):
        params=request.GET.copy();params['lang']=value
        return '?'+urlencode(params)
    from .contacts import public_contacts
    context={**public_contacts(),**context,'lang':lang,'vi_url':url('vi'),'en_url':url('en')}
    for key in ('services','articles'):
        if context.get(key) is not None:context[key]=[localized(obj,lang) for obj in context[key]]
    for key in ('item','service'):
        if context.get(key) is not None:context[key]=localized(context[key],lang)
    for key in ('title','label','error'):
        if key in context:context[key]=text(context[key],lang)
    if context.get('order'):
        snapshot=context['order'].snapshot
        context['order_title']=snapshot.get('title_en') or snapshot.get('title','') if lang=='en' else snapshot.get('title','')
    response=render(request,template,context)
    for name in ('sunny_lang','souvenirs_lang'):response.set_cookie(name,lang,max_age=31536000,httponly=True,samesite='Lax',secure=request.is_secure())
    patch_vary_headers(response,('Accept-Language','Cookie'))
    return response
