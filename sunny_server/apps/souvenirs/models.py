import uuid
from pathlib import Path
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

def product_slug():return uuid.uuid4().hex[:16]
def asset_path(instance,name):return 'souvenirs/'+str(instance.product_id)+'/'+uuid.uuid4().hex+Path(name).suffix.lower()

class Product(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    sku=models.CharField('Mã sản phẩm',max_length=60,unique=True)
    slug=models.SlugField(max_length=80,unique=True,default=product_slug,editable=False)
    name=models.CharField('Tên sản phẩm',max_length=180)
    category=models.CharField('Bộ sưu tập / nhóm sản phẩm',max_length=100,blank=True)
    summary=models.CharField('Giới thiệu ngắn',max_length=500,blank=True)
    story=models.TextField('Câu chuyện sản phẩm',blank=True)
    name_en=models.CharField('English — name',blank=True,max_length=180)
    category_en=models.CharField('English — category',blank=True,max_length=100)
    summary_en=models.CharField('English — summary',blank=True,max_length=500)
    story_en=models.TextField('English — story',blank=True)
    price=models.DecimalField('Giá bán (đồng)',max_digits=14,decimal_places=0,validators=[MinValueValidator(0)])
    cost=models.DecimalField('Giá vốn (nội bộ)',max_digits=14,decimal_places=0,default=0,validators=[MinValueValidator(0)])
    published=models.BooleanField('Hiển thị cho khách và cho phép bán',default=False)
    sort_order=models.PositiveIntegerField('Thứ tự',default=0)
    version=models.PositiveIntegerField(default=1)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['sort_order','name']
        permissions=[('manage_catalog','Quản lý sản phẩm, hình ảnh, video và bài viết Souvenirs'),('sell','Tạo đơn và xác nhận thu tiền Souvenirs tại quầy'),('view_reports','Xem doanh thu Souvenirs của tất cả nhân viên')]
    def __str__(self):return self.name
    @property
    def cover(self):return next((asset for asset in self.assets.all() if asset.kind=='image'),None)

class Asset(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='assets')
    kind=models.CharField('Loại nội dung',max_length=8,choices=[('image','Hình ảnh'),('video','Video MP4/WebM')])
    file=models.FileField('Tệp tải lên',upload_to=asset_path)
    caption=models.CharField('Chú thích',max_length=250,blank=True)
    caption_en=models.CharField('English — caption',blank=True,max_length=250)
    position=models.PositiveIntegerField('Thứ tự',default=0)
    class Meta:ordering=['position','id']

class Article(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='articles')
    title=models.CharField('Tiêu đề bài viết',max_length=180)
    body=models.TextField('Nội dung bài viết')
    title_en=models.CharField('English — title',max_length=180,blank=True)
    body_en=models.TextField('English — article',blank=True)
    position=models.PositiveIntegerField('Thứ tự',default=0)
    class Meta:ordering=['position','id']

class SaleOrder(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    request_id=models.UUIDField(unique=True)
    fingerprint=models.CharField(max_length=64)
    seller=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    seller_name=models.CharField(max_length=150)
    status=models.CharField(max_length=12,default='pending',choices=[('pending','Chờ thanh toán'),('paid','Đã thanh toán'),('cancelled','Đã hủy')])
    total=models.DecimalField(max_digits=16,decimal_places=0)
    cost_total=models.DecimalField(max_digits=16,decimal_places=0,default=0)
    payment_method=models.CharField(max_length=20,blank=True)
    card_fee=models.JSONField(default=dict,blank=True)
    note=models.CharField(max_length=1000,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    paid_at=models.DateTimeField(null=True,blank=True)
    paid_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True,related_name='souvenir_receipts')
    revision=models.PositiveIntegerField(default=0)
    deleted_at=models.DateTimeField(null=True,blank=True)
    history=models.JSONField(default=list,blank=True)
    class Meta:
        permissions=[('edit_orders','Sửa đơn hàng Souvenirs'),('delete_orders','Xóa đơn hàng Souvenirs')]
    @property
    def code(self):return 'SV-'+timezone.localtime(self.created_at).strftime('%Y%m%d')+'-'+self.id.hex[:12].upper()

class SaleLine(models.Model):
    order=models.ForeignKey(SaleOrder,on_delete=models.CASCADE,related_name='lines')
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    sku=models.CharField(max_length=60)
    name=models.CharField(max_length=180)
    quantity=models.PositiveIntegerField()
    unit_price=models.DecimalField(max_digits=14,decimal_places=0)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=0)
    @property
    def subtotal(self):return self.unit_price*self.quantity
