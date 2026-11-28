from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from PIL import Image
from apps.legacy.models import Workspace
from .models import Service,Article,OnlinePrice,OnlineOrder,ServiceOption,CartOrder,ServiceFAQ,ServiceTicketGroup

class WebsiteAdmin(admin.ModelAdmin):
    class Media:
        css={'all':('css/online_management.css',)}

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
from .richtext import RichTextWidget,MARKER,sanitize

class ServiceForm(ImageCheckForm):
    class Meta:
        model=Service
        fields='__all__'
        widgets={'body':RichTextWidget(),'body_en':RichTextWidget()}
    def clean_body(self):
        value=self.cleaned_data['body']
        return MARKER+sanitize(value[len(MARKER):]) if value.startswith(MARKER) else value
    def clean_body_en(self):
        value=self.cleaned_data.get('body_en','')
        return MARKER+sanitize(value[len(MARKER):]) if value.startswith(MARKER) else value
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

from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

class GroupOptionForm(ServiceOptionForm):
    class Meta:
        model=ServiceOption
        fields=['ticket_id','audience','published_price','online_price','strike_published_price','active','sort_order']
    def __init__(self,*args,group=None,**kwargs):
        self.parent_group=group
        super().__init__(*args,**kwargs)
        if group:
            self.instance.service_id=group.service_id
            self.instance.group=group
        self.fields['audience'].required=True
        self.fields['online_price'].required=True
        self.fields['online_price'].help_text='Giá mặc định cho Digital. Khách thanh toán theo giá này.'
        if self.instance.pk and self.instance.online_price is None:self.fields['online_price'].help_text+=' Vé cũ vẫn dùng kỳ giá đã lưu cho đến khi bạn nhập giá mặc định tại đây.'
        self.fields['ticket_id'].label='Vé từ hệ thống'
    def clean(self):
        values=super().clean()
        if self.parent_group:
            self.instance.group_name=self.parent_group.name
            self.instance.group_name_en=self.parent_group.name_en
            self.instance.title=self.parent_group.name+' · '+dict(ServiceOption._meta.get_field('audience').choices).get(values.get('audience'),'')
        return values

class GroupOptionFormSet(BaseInlineFormSet):
    def get_form_kwargs(self,index):
        values=super().get_form_kwargs(index);values['group']=self.instance;return values
    def clean(self):
        super().clean()
        seen=set()
        for form in self.forms:
            if not form.cleaned_data or form.errors:continue
            if form.cleaned_data.get('active'):
                audience=form.cleaned_data.get('audience')
                if audience in seen:raise ValidationError('Mỗi nhóm khách chỉ có một vé đang bán trong nhóm này.')
                seen.add(audience)

class GroupOptionInline(admin.StackedInline):
    model=ServiceOption
    fk_name='group'
    form=GroupOptionForm
    formset=GroupOptionFormSet
    extra=0
    can_delete=False
    fields=[('ticket_id','audience'),('published_price','online_price'),'strike_published_price',('active','sort_order')]
    verbose_name='Vé và giá Digital'
    verbose_name_plural='Các vé trong nhóm — chọn vé gốc và nhập giá ngay tại đây'
    def has_view_permission(self,request,obj=None):return request.user.has_perm('online.view_service') or request.user.has_perm('online.change_service')
    def has_change_permission(self,request,obj=None):return request.user.has_perm('online.change_service')
    def has_add_permission(self,request,obj=None):return request.user.has_perm('online.change_service')

class TicketGroupFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        names=set()
        for form in self.forms:
            if not form.cleaned_data or form.errors:continue
            name=form.cleaned_data.get('name','').strip().casefold()
            if name in names:raise ValidationError('Tên nhóm vé không được trùng trong dịch vụ.')
            names.add(name)

class TicketGroupInline(admin.TabularInline):
    model=ServiceTicketGroup
    formset=TicketGroupFormSet
    extra=0
    can_delete=False
    fields=['name','name_en','sort_order','tickets_link']
    readonly_fields=['tickets_link']
    verbose_name='Nhóm vé'
    verbose_name_plural='Nhóm vé — lưu nhóm rồi bấm Vé & giá để khai báo'
    def tickets_link(self,obj):
        if not obj.pk:return 'Lưu dịch vụ để khai báo vé và giá.'
        return format_html('<a class="button" href="{}">Vé & giá ({}) →</a>',reverse('admin:online_serviceticketgroup_change',args=[obj.pk]),obj.options.count())
    tickets_link.short_description='Khai báo vé và giá'
    def has_view_permission(self,request,obj=None):return request.user.has_perm('online.view_service') or request.user.has_perm('online.change_service')
    def has_change_permission(self,request,obj=None):return request.user.has_perm('online.change_service')
    def has_add_permission(self,request,obj=None):return request.user.has_perm('online.change_service') or request.user.has_perm('online.add_service')

@admin.register(ServiceTicketGroup)
class TicketGroupAdmin(WebsiteAdmin):
    fields=['service','name','name_en','sort_order','service_link']
    readonly_fields=['service','service_link']
    inlines=[GroupOptionInline]
    def get_model_perms(self,request):return {}
    def has_view_permission(self,request,obj=None):return request.user.has_perm('online.view_service') or request.user.has_perm('online.change_service')
    def has_change_permission(self,request,obj=None):return request.user.has_perm('online.change_service')
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
    def service_link(self,obj):return format_html('<a href="{}?tab=tickets">← Quay lại dịch vụ</a>',reverse('admin:online_service_change',args=[obj.service_id]))
    service_link.short_description='Dịch vụ'
    class Media:
        css={'all':('css/online_management.css',)}

class ServiceFAQInline(admin.StackedInline):
    model=ServiceFAQ
    extra=0
    fields=['question','keywords','answer','question_en','answer_en','active']

@admin.register(Service)
class ServiceAdmin(WebsiteAdmin):
    form=ServiceForm
    change_form_template='admin/online/service/change_form.html'
    inlines=[TicketGroupInline]
    exclude=['ticket_id']
    fieldsets=[
        ('Thông tin dịch vụ',{'fields':['title','slug','summary','image']}),
        ('Bài giới thiệu tiếng Việt',{'fields':['body']}),
        ('Nội dung tiếng Anh',{'fields':['title_en','summary_en','body_en']}),
        ('Hiển thị & giá giới thiệu',{'fields':['published','sort_order','card_price_source','card_price_option']}),
    ]
    class Media:
        css={'all':('css/online_management.css',)}
        js=('js/online_management.js',)
    def get_form(self,request,obj=None,**kwargs):
        form=super().get_form(request,obj,**kwargs)
        form.base_fields['card_price_source'].choices=[('auto','Tự chọn giá thấp nhất'),('option','Chọn vé để hiển thị Giá từ')]
        return form
    list_display=['title','published','sort_order']
    list_filter=['published']
    prepopulated_fields={'slug':('title',)}
@admin.register(Article)
class ArticleAdmin(WebsiteAdmin):
    form=ArticleForm
    list_display=['title','published','created_at']
    list_filter=['published']
    prepopulated_fields={'slug':('title',)}
@admin.register(OnlinePrice)
class OnlinePriceAdmin(WebsiteAdmin):
    def get_model_perms(self,request):return {}
    list_display=['service','option','price','starts_on','ends_on','active']
    list_filter=['active','service']
@admin.register(OnlineOrder)
class OnlineOrderAdmin(WebsiteAdmin):
    def get_model_perms(self,request):return {}
    list_display=['code','customer_name','service','visit_date','qty','total','status','created_at']
    list_filter=['status','visit_date']
    search_fields=['customer_name','email','phone','booking_id']
    readonly_fields=[f.name for f in OnlineOrder._meta.fields]
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
    def has_change_permission(self,request,obj=None):return False

from .models import SiteContact
@admin.register(SiteContact)
class SiteContactAdmin(WebsiteAdmin):
    fields=['facebook_url','tiktok_url','google_maps_url','whatsapp_url','zalo_url','line_url']
    def has_add_permission(self,request):return super().has_add_permission(request) and not SiteContact.objects.exists()
    def has_delete_permission(self,request,obj=None):return False

@admin.register(ServiceOption)
class ServiceOptionAdmin(WebsiteAdmin):
    def get_model_perms(self,request):return {}
    form=ServiceOptionForm
    list_display=['title','service','group_name','audience','ticket_id','active']
    list_filter=['service','audience','active']
    search_fields=['title','ticket_id']

@admin.register(CartOrder)
class CartOrderAdmin(WebsiteAdmin):
    list_display=['code','customer_name','email','total','payment_method','status','email_state','created_at','processing_link']
    list_filter=['status','payment_method','email_state','created_at']
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
class ServiceFAQAdmin(WebsiteAdmin):
    def get_model_perms(self,request):return {}
    list_display=['question','service','active','updated_at']
    list_filter=['service','active']
    search_fields=['question','question_en','keywords','answer']
