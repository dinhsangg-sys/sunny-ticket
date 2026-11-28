import uuid
from django.db import models
from django.core.exceptions import ValidationError

class Service(models.Model):
    title=models.CharField('Tên dịch vụ',max_length=180)
    slug=models.SlugField(unique=True,max_length=180)
    ticket_id=models.CharField('Loại vé mặc định trong Ticket Management',max_length=120,blank=True)
    summary=models.CharField('Giới thiệu ngắn',max_length=400)
    body=models.TextField('Giới thiệu / điều kiện sử dụng')
    title_en=models.CharField('Tên / tiêu đề tiếng Anh',max_length=180,blank=True)
    summary_en=models.CharField('Giới thiệu ngắn tiếng Anh',max_length=400,blank=True)
    body_en=models.TextField('Nội dung / điều kiện tiếng Anh',blank=True)
    image=models.ImageField('Ảnh giới thiệu',upload_to='online/content/',blank=True)
    published=models.BooleanField('Hiển thị công khai',default=False)
    sort_order=models.PositiveIntegerField('Thứ tự',default=0)
    card_price_source=models.CharField('Giá giới thiệu trên thẻ',max_length=12,choices=[('auto','Tự chọn giá thấp nhất đang có thể đặt'),('default','Dùng loại vé mặc định'),('option','Chọn một lựa chọn vé')],default='auto')
    card_price_option=models.ForeignKey('ServiceOption',on_delete=models.SET_NULL,null=True,blank=True,related_name='+',verbose_name='Loại vé làm giá giới thiệu')
    class Meta:
        ordering=['sort_order','title']
        verbose_name='Dịch vụ online'
        verbose_name_plural='Dịch vụ online'
    def __str__(self):return self.title
    def clean(self):
        if self.card_price_source=='option':
            if not self.card_price_option_id:raise ValidationError({'card_price_option':'Chọn loại vé để giới thiệu.'})
            if not self.pk or self.card_price_option.service_id!=self.pk:raise ValidationError({'card_price_option':'Loại vé phải thuộc dịch vụ này.'})

class Article(models.Model):
    title=models.CharField('Tiêu đề',max_length=180)
    slug=models.SlugField(unique=True,max_length=180)
    summary=models.CharField('Tóm tắt',max_length=400)
    body=models.TextField('Nội dung')
    title_en=models.CharField('Tiêu đề tiếng Anh',max_length=180,blank=True)
    summary_en=models.CharField('Tóm tắt tiếng Anh',max_length=400,blank=True)
    body_en=models.TextField('Nội dung tiếng Anh',blank=True)
    image=models.ImageField('Ảnh bài viết',upload_to='online/content/',blank=True)
    published=models.BooleanField('Xuất bản',default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created_at']
        verbose_name='Bài viết du lịch'
        verbose_name_plural='Bài viết du lịch'
    def __str__(self):return self.title

class OnlinePrice(models.Model):
    service=models.ForeignKey(Service,on_delete=models.PROTECT,verbose_name='Dịch vụ')
    option=models.ForeignKey('ServiceOption',on_delete=models.PROTECT,null=True,blank=True,verbose_name='Lựa chọn vé (trống = vé mặc định)')
    price=models.PositiveBigIntegerField('Giá bán online / vé (đồng)')
    starts_on=models.DateField('Từ ngày sử dụng')
    ends_on=models.DateField('Đến ngày sử dụng',null=True,blank=True)
    active=models.BooleanField('Đang áp dụng',default=True)
    class Meta:
        ordering=['service','-starts_on']
        verbose_name='Giá vé online'
        verbose_name_plural='Bảng giá online riêng'
    def clean(self):
        if self.option_id and self.option.service_id!=self.service_id:raise ValidationError('Lựa chọn vé phải thuộc dịch vụ đã chọn.')
        if self.price is not None and (self.price<=0 or self.price>100000000):raise ValidationError('Giá cần từ 1 đến 100.000.000 đồng.')
        if self.ends_on and self.starts_on and self.ends_on<self.starts_on:raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu.')
        if self.active and self.service_id and self.starts_on:
            rows=OnlinePrice.objects.filter(service_id=self.service_id,option_id=self.option_id,active=True).exclude(pk=self.pk)
            rows=rows.filter(models.Q(ends_on__isnull=True)|models.Q(ends_on__gte=self.starts_on))
            if self.ends_on:rows=rows.filter(starts_on__lte=self.ends_on)
            if rows.exists():raise ValidationError('Khoảng giá online bị trùng. Kết thúc kỳ giá cũ trước khi thêm kỳ mới.')
    def __str__(self):return str(self.service)+' — '+str(self.price)

class OnlineOrder(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    request_id=models.UUIDField(unique=True)
    session_hash=models.CharField(max_length=64)
    fingerprint=models.CharField(max_length=64)
    service=models.ForeignKey(Service,on_delete=models.PROTECT)
    option=models.ForeignKey('ServiceOption',on_delete=models.PROTECT,null=True,blank=True)
    cart=models.ForeignKey('CartOrder',on_delete=models.PROTECT,null=True,blank=True,related_name='lines')
    customer_name=models.CharField(max_length=120)
    email=models.EmailField()
    phone=models.CharField(max_length=30)
    visit_date=models.DateField()
    qty=models.PositiveIntegerField()
    unit_price=models.PositiveBigIntegerField()
    total=models.PositiveBigIntegerField()
    snapshot=models.JSONField()
    status=models.CharField(max_length=20,default='pending')
    intent=models.OneToOneField('legacy.SePayIntent',on_delete=models.PROTECT,null=True,blank=True)
    booking_id=models.CharField(max_length=120,blank=True)
    assigned_to=models.ForeignKey('accounts.User',on_delete=models.PROTECT,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    paid_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=['-created_at']
        permissions=[('process_orders','Xử lý đơn online và gửi vé cho khách')]
        verbose_name='Đơn vé online'
        verbose_name_plural='Đơn vé online'
    @property
    def code(self):return 'ON-'+self.id.hex[:12].upper()
    def __str__(self):return self.code

class ServiceTicketGroup(models.Model):
    service=models.ForeignKey(Service,on_delete=models.PROTECT,related_name='ticket_groups',verbose_name='Dịch vụ')
    name=models.CharField('Tên nhóm vé',max_length=100)
    name_en=models.CharField('Tên tiếng Anh',max_length=100,blank=True)
    sort_order=models.PositiveIntegerField('Thứ tự',default=0)
    class Meta:
        ordering=['sort_order','pk']
        verbose_name='Nhóm vé của dịch vụ'
        verbose_name_plural='Nhóm vé của dịch vụ'
        constraints=[models.UniqueConstraint(fields=['service','name'],name='online_unique_service_group')]
    def __str__(self):return self.name
    def clean(self):
        self.name=self.name.strip()
        if not self.name:raise ValidationError({'name':'Nhập tên nhóm vé.'})
        if self.service_id and ServiceTicketGroup.objects.filter(service_id=self.service_id,name__iexact=self.name).exclude(pk=self.pk).exists():raise ValidationError({'name':'Dịch vụ đã có nhóm vé với tên này.'})

class ServiceOption(models.Model):
    service=models.ForeignKey(Service,on_delete=models.PROTECT,related_name='options',verbose_name='Dịch vụ')
    group=models.ForeignKey(ServiceTicketGroup,on_delete=models.PROTECT,null=True,blank=True,related_name='options',verbose_name='Nhóm vé')
    online_price=models.PositiveBigIntegerField('Giá online mặc định (đ)',null=True,blank=True)
    published_price=models.PositiveBigIntegerField('Giá công bố (đ)',null=True,blank=True)
    strike_published_price=models.BooleanField('Gạch ngang giá công bố',default=False)
    title=models.CharField('Tên lựa chọn (vd ECO · Người lớn)',max_length=180)
    title_en=models.CharField('Tên lựa chọn tiếng Anh',max_length=180,blank=True)
    ticket_id=models.CharField('Loại vé trong Ticket Management',max_length=120)
    group_name=models.CharField('Nhóm loại vé (ECO / HIGH / VIP...)',max_length=100,blank=True)
    group_name_en=models.CharField('Nhóm loại vé tiếng Anh',max_length=100,blank=True)
    audience=models.CharField('Nhóm khách',max_length=10,choices=[('adult','Người lớn'),('child','Trẻ em'),('senior','Người cao tuổi')],blank=True)
    active=models.BooleanField('Đang bán',default=True)
    sort_order=models.PositiveIntegerField('Thứ tự',default=0)
    class Meta:
        ordering=['sort_order','pk']
        verbose_name='Lựa chọn vé online'
        verbose_name_plural='Lựa chọn vé online'
    def clean(self):
        if self.group_id:
            if self.group.service_id!=self.service_id:raise ValidationError('Nhóm vé phải thuộc dịch vụ này.')
            self.group_name=self.group.name;self.group_name_en=self.group.name_en
        for field in ('online_price','published_price'):
            value=getattr(self,field)
            if value is not None and not 0<value<=100000000:raise ValidationError({field:'Giá cần từ 1 đến 100.000.000 đồng.'})
        if self.strike_published_price and (not self.published_price or not self.online_price or self.online_price>=self.published_price):raise ValidationError({'strike_published_price':'Chỉ gạch ngang khi giá online thấp hơn giá công bố.'})
        self.group_name=self.group_name.strip()
        if self.group_name and not self.audience:raise ValidationError({'audience':'Chọn Người lớn, Trẻ em hoặc Người cao tuổi cho nhóm vé.'})
        if self.audience and not self.group_name:raise ValidationError({'group_name':'Nhập nhóm loại vé, ví dụ ECO.'})
        if self.active and self.group_name and self.audience and self.service_id and ServiceOption.objects.filter(service_id=self.service_id,group_name__iexact=self.group_name,audience=self.audience,active=True).exclude(pk=self.pk).exists():raise ValidationError('Nhóm loại vé đã có lựa chọn đang bán cho nhóm khách này.')
    @property
    def display_title(self):
        return (self.group.name if self.group_id else self.group_name)+' · '+self.get_audience_display() if (self.group_id or self.group_name) and self.audience else self.title
    @property
    def display_title_en(self):
        labels={'adult':'Adult','child':'Child','senior':'Senior'}
        return ((self.group.name_en or self.group.name) if self.group_id else (self.group_name_en or self.group_name))+' · '+labels.get(self.audience,self.audience) if self.group_name and self.audience else (self.title_en or self.title)
    def __str__(self):return str(self.service)+' — '+self.display_title

class CartOrder(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    request_id=models.UUIDField(unique=True)
    session_hash=models.CharField(max_length=64)
    fingerprint=models.CharField(max_length=64)
    customer_name=models.CharField(max_length=120)
    email=models.EmailField()
    phone=models.CharField(max_length=30)
    total=models.PositiveBigIntegerField()
    language=models.CharField(max_length=2,default='en')
    status=models.CharField(max_length=20,default='pending')
    intent=models.OneToOneField('legacy.SePayIntent',on_delete=models.PROTECT,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    paid_at=models.DateTimeField(null=True,blank=True)
    email_state=models.CharField(max_length=20,default='pending')
    send_started_at=models.DateTimeField(null=True,blank=True)
    emailed_at=models.DateTimeField(null=True,blank=True)
    processed_by=models.ForeignKey('accounts.User',on_delete=models.PROTECT,null=True,blank=True)
    processing_note=models.TextField(blank=True)
    notification_state=models.CharField(max_length=20,default='pending')
    payment_method=models.CharField('Phương thức thanh toán',max_length=20,default='',blank=True,choices=[('','Chưa chọn'),('bank_transfer','QR chuyển khoản'),('cash','Tiền mặt khi giao vé')])
    cash_requested_at=models.DateTimeField(null=True,blank=True)
    delivery_note=models.CharField('Thông tin giao vé tại Đà Nẵng',max_length=500,blank=True)
    class Meta:
        ordering=['-created_at']
        permissions=[('collect_cash_orders','Xác nhận giao vé và thu tiền mặt đơn online')]
        verbose_name='Đơn giỏ hàng online'
        verbose_name_plural='Đơn giỏ hàng online / Chờ gửi vé'
    @property
    def code(self):return 'SC-'+self.id.hex[:12].upper()
    def __str__(self):return self.code
    @property
    def can_reconcile(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.email_state in ('pending','uncertain') or (self.email_state=='sending' and self.send_started_at is not None and self.send_started_at<timezone.now()-timedelta(minutes=5))
    @property
    def delivery_label(self):
        if self.payment_method=='cash' and self.status=='pending':return 'Chờ liên hệ giao vé / Thu tiền tại Đà Nẵng'
        if self.payment_method=='cash' and self.email_state=='external':return 'Đã giao vé và thu tiền mặt'
        return {'pending':'Chờ xử lý / Gửi vé','sending':'Đang gửi email','sent':'Đã gửi qua hệ thống','external':'Đã xác nhận gửi bên ngoài','uncertain':'Chưa rõ kết quả gửi — cần đối soát'}.get(self.email_state,self.email_state)
    @property
    def notification_label(self):
        return {'pending':'Chờ thông báo','sent':'Đã thông báo quản trị','unconfigured':'Chưa có email quản trị nhận thông báo','error':'Gửi thông báo lỗi — kiểm tra hộp thư cấu hình'}.get(self.notification_state,self.notification_state)

def private_ticket_storage():
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    return FileSystemStorage(location=getattr(settings,'ONLINE_TICKET_ROOT',settings.BASE_DIR/'private_online_tickets'))

def ticket_upload_path(instance,filename):return 'online/private-tickets/'+str(instance.order_id)+'/'+uuid.uuid4().hex+instance.extension

class OrderTicket(models.Model):
    order=models.ForeignKey(CartOrder,on_delete=models.PROTECT,related_name='tickets')
    file=models.FileField(upload_to=ticket_upload_path,storage=private_ticket_storage)
    name=models.CharField(max_length=180)
    extension=models.CharField(max_length=8)
    content_type=models.CharField(max_length=50)
    size=models.PositiveIntegerField()
    uploaded_by=models.ForeignKey('accounts.User',on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)

class SiteContact(models.Model):
    id=models.PositiveSmallIntegerField(primary_key=True,default=1,editable=False)
    facebook_url=models.URLField('Facebook',max_length=500,blank=True)
    tiktok_url=models.URLField('TikTok',max_length=500,blank=True)
    google_maps_url=models.URLField('Google Maps',max_length=500,blank=True)
    whatsapp_url=models.URLField('WhatsApp',max_length=500,blank=True,help_text='Ví dụ https://wa.me/849xxxxxxxx, dùng số quốc tế bỏ dấu + và số 0 đầu.')
    zalo_url=models.URLField('Zalo',max_length=500,blank=True,help_text='Đường dẫn Zalo cá nhân hoặc OA chính thức.')
    line_phone=models.CharField('Số điện thoại LINE',max_length=30,blank=True,help_text='Hiển thị số liên hệ khi chưa có link LINE; không tự tạo liên kết từ số điện thoại.')
    line_url=models.URLField('LINE',max_length=500,blank=True,help_text='Đường dẫn LINE chính thức dạng https://line.me/... hoặc https://lin.ee/...')
    class Meta:
        verbose_name='Liên hệ & kênh Sunny'
        verbose_name_plural='Liên hệ & kênh Sunny'
    def clean(self):
        from .contacts import valid_contact_url
        errors={}
        for field in ('facebook_url','tiktok_url','google_maps_url','whatsapp_url','zalo_url','line_url'):
            value=getattr(self,field,'').strip();setattr(self,field,value)
            if value and not valid_contact_url(field,value):errors[field]='Dùng liên kết HTTPS đúng kênh, không chứa tên đăng nhập hoặc mật khẩu.'
        import re
        self.line_phone=re.sub(r'[ ()-]','',self.line_phone)
        if self.line_phone and not re.fullmatch(r'\+[1-9][0-9]{7,14}',self.line_phone):errors['line_phone']='Nhập số quốc tế, ví dụ +84932548145.'
        if self.pk!=1:errors['__all__']='Chỉ sử dụng một cấu hình liên hệ Sunny.'
        if errors:raise ValidationError(errors)
    def __str__(self):return 'Sunny — Kênh chính thức & liên hệ'


class ServiceFAQ(models.Model):
    service=models.ForeignKey(Service,on_delete=models.CASCADE,related_name='chat_faqs',verbose_name='Dịch vụ')
    question=models.CharField('Câu hỏi',max_length=240)
    answer=models.TextField('Trả lời đã duyệt',max_length=4000)
    keywords=models.CharField('Từ khóa (phân cách bằng dấu phẩy)',max_length=500,help_text='Ví dụ: giờ mở cửa, lịch diễn, opening hours. Không dùng từ quá chung như vé hoặc dịch vụ.')
    question_en=models.CharField('Câu hỏi tiếng Anh',max_length=240,blank=True)
    answer_en=models.TextField('Trả lời tiếng Anh',max_length=4000,blank=True)
    active=models.BooleanField('Cho phép bot sử dụng',default=False)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['pk']
        verbose_name='Câu hỏi tư vấn dịch vụ'
        verbose_name_plural='Chat Sunny — Câu hỏi / Từ khóa'
    def __str__(self):return str(self.service)+' — '+self.question
