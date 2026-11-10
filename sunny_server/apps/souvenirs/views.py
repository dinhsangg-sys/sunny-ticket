from decimal import Decimal
from datetime import date
import hashlib
from io import BytesIO
import json
import uuid
import unicodedata
from urllib.parse import urlparse, urlencode
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction,OperationalError,IntegrityError
from django.http import JsonResponse,Http404,HttpResponse,HttpResponseForbidden,FileResponse,StreamingHttpResponse
from django.shortcuts import render,get_object_or_404,redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET,require_POST,require_http_methods
from apps.legacy.access import full_access
from apps.legacy.models import Workspace
from apps.legacy.card_fees import quote_fee
from apps.audit.models import AuditLog
from .models import Product,Asset,SaleOrder,SaleLine
from .forms import ProductForm,Assets,Articles

def enabled():
    if not settings.SOUVENIRS_ENABLED:raise Http404()

def can(user,action):return user.is_authenticated and user.is_active and (user.is_superuser or user.role in ('admin','operator') and full_access(user) or user.has_perm('souvenirs.'+action))

def base_context(request):
    from apps.legacy.counter import permitted
    return {'base':'' if getattr(request,'urlconf',None)=='apps.souvenirs.public_urls' else '/souvenirs','can_manage':can(request.user,'manage_catalog'),'can_sell':can(request.user,'sell'),'can_report':can(request.user,'view_reports'),'report_visible':permitted(request.user,'report')}

def product_url(product):
    url=settings.SOUVENIRS_CATALOG_URL;parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('SOUVENIRS_CATALOG_URL cần là đường dẫn catalog HTTPS hợp lệ.')
    return url


def public_context(request):
    lang=request.GET.get('lang','vi')
    if lang not in ('vi','en'):lang='vi'
    def language_url(value):
        params=request.GET.copy();params['lang']=value
        return '?'+urlencode(params)
    return {**base_context(request),'lang':lang,'vi_url':language_url('vi'),'en_url':language_url('en')}

def translate_product(product,lang):
    for field in ('name','category','summary','story'):
        setattr(product,'display_'+field,(getattr(product,field+'_en') if lang=='en' else '') or getattr(product,field))
    for asset in product.assets.all():asset.display_caption=(asset.caption_en if lang=='en' else '') or asset.caption
    return product

@require_GET
@never_cache
def catalog(request):
    enabled();products=Product.objects.filter(published=True).prefetch_related('assets')
    q=request.GET.get('q','').strip()[:100];category=request.GET.get('category','').strip()[:100]
    categories=Product.objects.filter(published=True).exclude(category='').values_list('category',flat=True).distinct().order_by('category')
    if category:products=products.filter(category=category)
    if q:
        def searchable(value):return ''.join(c for c in unicodedata.normalize('NFD',value.casefold().replace('đ','d')) if not unicodedata.combining(c))
        needle=searchable(q);products=[p for p in products if needle in searchable(p.name+' '+p.name_en+' '+p.sku)]
    context=public_context(request)
    categories=[{'value':value,'label':(Product.objects.filter(published=True,category=value).exclude(category_en='').values_list('category_en',flat=True).first() if context['lang']=='en' else '') or value} for value in categories]
    products=[translate_product(p,context['lang']) for p in products]
    return render(request,'souvenirs/catalog.html',{**context,'products':products,'categories':categories,'q':q,'selected_category':category})

@require_GET
@never_cache
def detail(request,slug):
    enabled();product=get_object_or_404(Product.objects.prefetch_related('assets','articles'),slug=slug,published=True)
    context=public_context(request);translate_product(product,context['lang'])
    for article in product.articles.all():
        article.display_title=(article.title_en if context['lang']=='en' else '') or article.title
        article.display_body=(article.body_en if context['lang']=='en' else '') or article.body
    return render(request,'souvenirs/detail.html',{**context,'product':product,'intro_video':next((a for a in product.assets.all() if a.kind=='video'),None)})

@require_GET
@never_cache
def media(request,key):
    enabled();asset=get_object_or_404(Asset.objects.select_related('product'),pk=key)
    if not asset.product.published and not can(request.user,'manage_catalog'):raise Http404()
    if not asset.file:raise Http404()
    stream=asset.file.open('rb');size=asset.file.size;mime={'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp','mp4':'video/mp4','webm':'video/webm'}.get(asset.file.name.rsplit('.',1)[-1].lower(),'application/octet-stream')
    header=request.headers.get('Range','')
    if header:
        import re
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',header) if len(header)<=100 else None
        if not match or not any(match.groups()):stream.close();return HttpResponse(status=416,headers={'Content-Range':f'bytes */{size}'})
        start=int(match[1]) if match[1] else max(0,size-int(match[2]));end=min(int(match[2]),size-1) if match[1] and match[2] else size-1
        if start>=size or end<start:stream.close();return HttpResponse(status=416,headers={'Content-Range':f'bytes */{size}'})
        def chunks():
            try:
                stream.seek(start);remaining=end-start+1
                while remaining:
                    value=stream.read(min(65536,remaining))
                    if not value:break
                    remaining-=len(value);yield value
            finally:stream.close()
        response=StreamingHttpResponse(chunks(),status=206,content_type=mime);response['Content-Range']=f'bytes {start}-{end}/{size}';response['Content-Length']=end-start+1
    else:response=FileResponse(stream,content_type=mime)
    response['Accept-Ranges']='bytes';response['X-Content-Type-Options']='nosniff';return response

@login_required
@ensure_csrf_cookie
@never_cache
def management(request):
    enabled()
    if not any(can(request.user,action) for action in ('manage_catalog','sell','view_reports')):return HttpResponseForbidden('Chưa được cấp quyền Souvenirs.')
    return render(request,'souvenirs/management.html',{**base_context(request),'products':Product.objects.prefetch_related('assets') if can(request.user,'manage_catalog') else []})

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def edit_product(request,key=None):
    enabled()
    if not can(request.user,'manage_catalog'):return HttpResponseForbidden('Chưa được cấp quyền quản lý sản phẩm.')
    product=get_object_or_404(Product,pk=key) if key else Product()
    form=ProductForm(request.POST or None,instance=product,initial={'expected_version':product.version})
    assets=Assets(request.POST or None,request.FILES or None,instance=product,prefix='assets')
    articles=Articles(request.POST or None,instance=product,prefix='articles')
    if request.method=='POST':
        valid=form.is_valid();valid_assets=assets.is_valid();valid_articles=articles.is_valid()
        if valid and valid_assets and valid_articles:
            try:
                with transaction.atomic():
                    Workspace.objects.get_or_create(pk=1);Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
                    if key and Product.objects.get(pk=key).version!=form.cleaned_data['expected_version']:raise ValueError('Sản phẩm đã đổi. Tải lại trang trước khi sửa tiếp.')
                    product=form.save(commit=False);product.version+=1;product.save();assets.instance=product;assets.save();articles.instance=product;articles.save()
                    AuditLog.objects.create(user=request.user,action='souvenirs.product_save:'+str(product.pk))
                return redirect('/souvenirs/manage/')
            except (ValueError,OperationalError) as exc:form.add_error(None,str(exc))
            except IntegrityError:form.add_error(None,'Mã sản phẩm đã được sử dụng hoặc dữ liệu vừa thay đổi. Tải lại danh sách để kiểm tra.')
    return render(request,'souvenirs/product_form.html',{**base_context(request),'form':form,'assets':assets,'articles':articles,'product':product,'editing':bool(key)})

@login_required
@require_GET
@never_cache
def qr_label(request,key):
    enabled()
    if not can(request.user,'manage_catalog'):return HttpResponseForbidden('Chưa có quyền tạo tem QR sản phẩm.')
    product=get_object_or_404(Product,pk=key)
    try:url=product_url(product)
    except ValueError as exc:return HttpResponse(str(exc),status=400)
    if request.GET.get('format')=='png':
        import zxingcpp
        from PIL import Image
        pixels=zxingcpp.write_barcode_to_image(zxingcpp.create_barcode(url,zxingcpp.BarcodeFormat.QRCode),scale=10,add_quiet_zones=True)
        height,width=memoryview(pixels).shape;image=Image.frombytes('L',(width,height),bytes(pixels));result=BytesIO();image.save(result,format='PNG')
        response=HttpResponse(result.getvalue(),content_type='image/png');response['Content-Disposition']=('attachment' if request.GET.get('download')=='1' else 'inline')+'; filename="souvenir-'+product.slug+'.png"';return response
    return render(request,'souvenirs/label.html',{**base_context(request),'product':product,'public_url':url})

def order_data(order):
    return {'id':str(order.pk),'code':order.code,'status':order.status,'createdAt':order.created_at.isoformat(),'paidAt':order.paid_at.isoformat() if order.paid_at else None,'seller':order.seller_name,'total':float(order.total),'paymentMethod':order.payment_method,'fee':float(order.card_fee.get('feeAmount',0)),'net':float(order.total)-float(order.card_fee.get('feeAmount',0)) if order.status=='paid' else 0,'note':order.note,'lines':[{'sku':line.sku,'name':line.name,'quantity':line.quantity,'unitPrice':float(line.unit_price),'subtotal':float(line.subtotal)} for line in order.lines.all()]}

def own_order(request,key):
    query=SaleOrder.objects.select_related('seller').prefetch_related('lines')
    if not can(request.user,'view_reports'):query=query.filter(seller=request.user)
    return get_object_or_404(query,pk=key)

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def sales(request):
    enabled()
    if not can(request.user,'sell'):return JsonResponse({'error':'Chưa có quyền bán hàng lưu niệm.'},status=403)
    if request.method=='GET':return JsonResponse({'products':[{'id':str(p.pk),'sku':p.sku,'name':p.name,'price':float(p.price)} for p in Product.objects.filter(published=True)],'orders':[order_data(o) for o in SaleOrder.objects.filter(seller=request.user).prefetch_related('lines').order_by('-created_at')[:100]]})
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict) or set(body)!={'requestId','items','note'}:raise ValueError('Dữ liệu đơn hàng không hợp lệ.')
        request_id=uuid.UUID(body['requestId']);items=body['items'];note=body['note']
        if not isinstance(note,str) or len(note)>1000 or not isinstance(items,list) or not 1<=len(items)<=50:raise ValueError('Đơn cần từ 1–50 mặt hàng, ghi chú tối đa 1000 ký tự.')
        normalized=[];seen=set()
        for item in items:
            if not isinstance(item,dict) or set(item)!={'product','quantity','expectedPrice'}:raise ValueError('Dòng hàng không hợp lệ.')
            key=str(uuid.UUID(item['product']));qty=item['quantity']
            if type(qty) is not int or not 1<=qty<=10000 or key in seen:raise ValueError('Số lượng phải từ 1–10000, không trùng dòng sản phẩm.')
            from apps.legacy.pricing import amount
            expected=amount(item['expectedPrice'])
            seen.add(key);normalized.append({'product':key,'quantity':qty,'expectedPrice':str(expected)})
        fingerprint=hashlib.sha256(json.dumps({'items':sorted(normalized,key=lambda i:i['product']),'note':note},sort_keys=True).encode()).hexdigest()
        with transaction.atomic():
            Workspace.objects.get_or_create(pk=1);Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            old=SaleOrder.objects.filter(request_id=request_id).first()
            if old:
                if old.seller_id!=request.user.pk or old.fingerprint!=fingerprint:raise ValueError('Mã yêu cầu đã dùng cho đơn khác. Tải lại để kiểm tra.')
                return JsonResponse({'order':order_data(old),'duplicate':True})
            products={str(p.pk):p for p in Product.objects.filter(pk__in=seen,published=True)}
            if len(products)!=len(seen):raise ValueError('Có sản phẩm ngừng bán hoặc không còn tồn tại.')
            if any(products[i['product']].price!=Decimal(i['expectedPrice']) for i in normalized):raise ValueError('Giá sản phẩm đã thay đổi. Tải lại danh mục và kiểm tra giá trước khi tạo đơn.')
            total=sum(products[i['product']].price*i['quantity'] for i in normalized);cost=sum(products[i['product']].cost*i['quantity'] for i in normalized)
            if total>100000000000000 or cost>100000000000000:raise ValueError('Tổng tiền vượt giới hạn.')
            order=SaleOrder.objects.create(request_id=request_id,fingerprint=fingerprint,seller=request.user,seller_name=request.user.get_full_name() or request.user.username,total=total,cost_total=cost,note=note)
            for item in normalized:
                p=products[item['product']];SaleLine.objects.create(order=order,product=p,sku=p.sku,name=p.name,quantity=item['quantity'],unit_price=p.price,unit_cost=p.cost)
            AuditLog.objects.create(user=request.user,action='souvenirs.order_create:'+str(order.pk))
        return JsonResponse({'order':order_data(order)},status=201)
    except (ValueError,TypeError,KeyError,AttributeError,ValidationError) as exc:return JsonResponse({'error':str(exc)},status=400)
    except (OperationalError,IntegrityError):return JsonResponse({'error':'Đang lưu đơn. Tải lại danh sách trước khi thử lại.'},status=409)

@login_required
@never_cache
@require_POST
def order_action(request,key):
    enabled()
    if not can(request.user,'sell'):return JsonResponse({'error':'Chưa có quyền thu tiền Souvenirs.'},status=403)
    try:
        body=json.loads(request.body)
        if not isinstance(body,dict):raise ValueError('Dữ liệu không hợp lệ.')
        with transaction.atomic():
            Workspace.objects.get_or_create(pk=1);Workspace.objects.filter(pk=1).update(updated_at=timezone.now())
            order=own_order(request,key);action=body.get('action')
            if action=='quote':
                if set(body)!={'action','scheme','origin'} or order.status!='pending':raise ValueError('Đơn không còn chờ thanh toán.')
                return JsonResponse({'quote':quote_fee(body['scheme'],body['origin'],order.total)})
            if action=='cancel':
                if set(body)!={'action','confirmed'} or body['confirmed'] is not True or order.status=='paid':raise ValueError('Chỉ hủy đơn chưa thu tiền; đơn đã thu cần đối soát riêng.')
                order.status='cancelled';order.save(update_fields=['status']);AuditLog.objects.create(user=request.user,action='souvenirs.order_cancel:'+str(order.pk));return JsonResponse({'order':order_data(order)})
            if action!='pay' or set(body)-{'action','confirmed','method','cardFeeQuote'} or body.get('confirmed') is not True or body.get('method') not in ('cash','card','bank_transfer'):raise ValueError('Chọn phương thức và xác nhận đã thu đủ tiền thực tế.')
            if order.status=='paid':
                if order.payment_method!=body['method']:raise ValueError('Đơn đã thu bằng phương thức khác.')
                return JsonResponse({'order':order_data(order),'duplicate':True})
            if order.status!='pending':raise ValueError('Đơn đã hủy.')
            fee={}
            if body['method']=='card':
                given=body.get('cardFeeQuote')
                if not isinstance(given,dict):raise ValueError('Chọn đủ loại thẻ/nơi phát hành để tính phí.')
                fee=quote_fee(given.get('scheme'),given.get('origin'),order.total)
                if given!=fee:return JsonResponse({'error':'Biểu phí đã đổi. Tính lại trước khi xác nhận.'},status=409)
            elif body.get('cardFeeQuote'):raise ValueError('Phí thẻ chỉ áp dụng cho thanh toán thẻ.')
            order.status='paid';order.payment_method=body['method'];order.card_fee=fee;order.paid_at=timezone.now();order.paid_by=request.user;order.save(update_fields=['status','payment_method','card_fee','paid_at','paid_by']);AuditLog.objects.create(user=request.user,action='souvenirs.order_paid:'+str(order.pk))
        return JsonResponse({'order':order_data(order)})
    except (ValueError,TypeError,KeyError,ValidationError) as exc:return JsonResponse({'error':str(exc)},status=400)
    except OperationalError:return JsonResponse({'error':'Đang có thao tác lưu. Tải lại để kiểm tra.'},status=409)

@login_required
@require_GET
@never_cache
def report(request):
    enabled()
    if not can(request.user,'view_reports'):return JsonResponse({'error':'Chưa có quyền xem doanh thu Souvenirs.'},status=403)
    try:
        start=request.GET.get('from','');end=request.GET.get('to','')
        if start:date.fromisoformat(start)
        if end:date.fromisoformat(end)
        if start and end and start>end:raise ValueError('Từ ngày không thể sau Đến ngày.')
        orders=SaleOrder.objects.filter(status='paid').prefetch_related('lines').order_by('-paid_at')
        if start:orders=orders.filter(paid_at__date__gte=start)
        if end:orders=orders.filter(paid_at__date__lte=end)
        rows=[order_data(order)|{'cost':float(order.cost_total),'profit':float(order.total-order.cost_total)-float(order.card_fee.get('feeAmount',0))} for order in orders]
        totals={'orders':len(rows),'quantity':sum(line['quantity'] for row in rows for line in row['lines']),**{key:sum(row[key] for row in rows) for key in ('total','fee','net','cost','profit')}}
        return JsonResponse({'rows':rows,'totals':totals})
    except ValueError as exc:return JsonResponse({'error':str(exc)},status=400)
