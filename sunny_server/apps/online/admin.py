from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from PIL import Image
from apps.legacy.models import Workspace
from .models import Service,Article,OnlinePrice,OnlineOrder,ServiceOption,CartOrder,ServiceFAQ

class ImageCheckForm(forms.ModelForm):
    def clean_image(self):
        image=self.cleaned_data.get('image')
        if image and hasattr(image,'content_type'):
            if image.size>5*1024*1024:raise ValidationError('Ảnh tối đa 5 MB.')
            try:
                picture=Image.open(image);picture.verify()
                if picture.format not in ('JPEG','PNG','WEBP') or picture.width*picture.height>25000000:raise ValueError()
            except Exception:raise ValidationError('Chỉ dùng JPEG/PNG/WebP hợp lệ, tối đa 25 triệu điểm ảnh.')
            image.seek(0)
        return image
class ServiceForm(ImageCheckForm):
    class Meta:model=Service;fields='__all__'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
        choices=[(t['id'],t.get('name',t['id'])+' — '+t.get('product','')) for t in data.get('ticketTypes',[]) if t.get('active',True)]
        if self.instance.pk and self.instance.ticket_id not in dict(choices):choices.append((self.instance.ticket_id,self.instance.ticket_id+' (đã dừng)'))
        self.fields['card_price_option'].queryset=ServiceOption.objects.filter(service=self.instance) if self.instance.pk else ServiceOption.objects.none()
        self.fields['card_price_source'].label='Cách chọn giá giới thiệu'
        self.fields['card_price_option'].label='Loại vé hiển thị Giá từ'
        self.fields['card_price_source'].help_text='Để tự chọn một loại bất kỳ, chọn chế độ Chọn một lựa chọn vé rồi chọn loại ở ô bên dưới. Không bắt buộc chọn loại có giá thấp nhất.'
        self.fields['card_price_option'].help_text='Chọn chế độ ở trên; lưu dịch vụ và tạo lựa chọn/giá online trước, rồi quay lại chọn loại vé giới thiệu.'
        self.fields['ticket_id']=forms.ChoiceField(label='Loại vé mặc định (có thể bỏ trống nếu dùng lựa chọn vé)',required=False,choices=[('','Không dùng vé mặc định')]+choices)
class ArticleForm(ImageCheckForm):
    class Meta:model=Article;fields='__all__'
class ServiceOptionForm(forms.ModelForm):
    class Meta:model=ServiceOption;fields='__all__'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
        choices=[(t['id'],t.get('name',t['id'])+' — '+t.get('product','')) for t in data.get('ticketTypes',[]) if t.get('active',True)]
        if self.instance.pk and self.instance.ticket_id not in dict(choices):choices.append((self.instance.ticket_id,self.instance.ticket_id+' (đã dừng)'))
        self.fields['ticket_id']=forms.ChoiceField(label='Loại vé có sẵn',choices=[('','Chọn loại vé')]+choices)

class ServiceOptionInline(admin.TabularInline):
    model=ServiceOption
    form=ServiceOptionForm
    extra=0
    fields=['title','title_en','ticket_id','active','sort_order']

class ServiceFAQInline(admin.StackedInline):
    model=ServiceFAQ
    extra=0
    fields=['question','keywords','answer','question_en','answer_en','active']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    form=ServiceForm
    inlines=[ServiceOptionInline,ServiceFAQInline]
    list_display=['title','ticket_id','published','card_price_source','sort_order']
    list_filter=['published']
    prepopulated_fields={'slug':('title',)}
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form=ArticleForm
    list_display=['title','published','created_at']
    list_filter=['published']
    prepopulated_fields={'slug':('title',)}
@admin.register(OnlinePrice)
class OnlinePriceAdmin(admin.ModelAdmin):
    list_display=['service','option','price','starts_on','ends_on','active']
    list_filter=['active','service']
@admin.register(OnlineOrder)
class OnlineOrderAdmin(admin.ModelAdmin):
    list_display=['code','customer_name','service','visit_date','qty','total','status','created_at']
    list_filter=['status','visit_date']
    search_fields=['customer_name','email','booking_id']
    readonly_fields=[f.name for f in OnlineOrder._meta.fields]
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
    def has_change_permission(self,request,obj=None):return False

from .models import SiteContact
@admin.register(SiteContact)
class SiteContactAdmin(admin.ModelAdmin):
    fields=['facebook_url','tiktok_url','google_maps_url','whatsapp_url','zalo_url','line_url']
    def has_add_permission(self,request):return super().has_add_permission(request) and not SiteContact.objects.exists()
    def has_delete_permission(self,request,obj=None):return False

@admin.register(ServiceOption)
class ServiceOptionAdmin(admin.ModelAdmin):
    form=ServiceOptionForm
    list_display=['title','service','ticket_id','active']
    list_filter=['service','active']
    search_fields=['title','ticket_id']

@admin.register(CartOrder)
class CartOrderAdmin(admin.ModelAdmin):
    list_display=['code','customer_name','email','total','status','email_state','created_at','processing_link']
    list_filter=['status','email_state','created_at']
    search_fields=['email','customer_name','phone']
    readonly_fields=[f.name for f in CartOrder._meta.fields]+['processing_link']
    def processing_link(self,obj):
        from django.utils.html import format_html
        return format_html('<a href="/online/staff/cart/{}/">Xử lý đơn / Đính kèm / Gửi vé</a>',obj.pk)
    processing_link.short_description='Xử lý đơn'
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
    def has_change_permission(self,request,obj=None):return False

@admin.register(ServiceFAQ)
class ServiceFAQAdmin(admin.ModelAdmin):
    list_display=['question','service','active','updated_at']
    list_filter=['service','active']
    search_fields=['question','question_en','keywords','answer']
