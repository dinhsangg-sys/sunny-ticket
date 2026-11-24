import uuid
from django.db import models
from django.core.exceptions import ValidationError

class Service(models.Model):
    title=models.CharField('Tên dịch vụ',max_length=180)
    slug=models.SlugField(unique=True,max_length=180)
    ticket_id=models.CharField('Loại vé trong Ticket Management',max_length=120)
    summary=models.CharField('Giới thiệu ngắn',max_length=400)
    body=models.TextField('Giới thiệu / điều kiện sử dụng')
    image=models.ImageField('Ảnh giới thiệu',upload_to='online/content/',blank=True)
    published=models.BooleanField('Hiển thị công khai',default=False)
    sort_order=models.PositiveIntegerField('Thứ tự',default=0)
    class Meta:
        ordering=['sort_order','title']
        verbose_name='Dịch vụ online'
        verbose_name_plural='Dịch vụ online'
    def __str__(self):return self.title

class Article(models.Model):
    title=models.CharField('Tiêu đề',max_length=180)
    slug=models.SlugField(unique=True,max_length=180)
    summary=models.CharField('Tóm tắt',max_length=400)
    body=models.TextField('Nội dung')
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
    price=models.PositiveBigIntegerField('Giá bán online / vé (đồng)')
    starts_on=models.DateField('Từ ngày sử dụng')
    ends_on=models.DateField('Đến ngày sử dụng',null=True,blank=True)
    active=models.BooleanField('Đang áp dụng',default=True)
    class Meta:
        ordering=['service','-starts_on']
        verbose_name='Giá vé online'
        verbose_name_plural='Bảng giá online riêng'
    def clean(self):
        if self.price<=0 or self.price>100000000:raise ValidationError('Giá cần từ 1 đến 100.000.000 đồng.')
        if self.ends_on and self.starts_on and self.ends_on<self.starts_on:raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu.')
        if self.active and self.service_id and self.starts_on:
            rows=OnlinePrice.objects.filter(service_id=self.service_id,active=True).exclude(pk=self.pk)
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
