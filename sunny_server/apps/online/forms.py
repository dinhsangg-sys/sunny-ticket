from datetime import timedelta
from django import forms
from django.utils import timezone
class CheckoutForm(forms.Form):
    request_id=forms.UUIDField(widget=forms.HiddenInput)
    visit_date=forms.DateField(label='Ngày sử dụng',widget=forms.DateInput(attrs={'type':'date'}))
    qty=forms.IntegerField(label='Số lượng vé',min_value=1,max_value=20,initial=1)
    customer_name=forms.CharField(label='Họ tên khách',max_length=120)
    email=forms.EmailField(label='Email nhận vé',max_length=254)
    phone=forms.RegexField(label='Số điện thoại',regex=r'^[+0-9 ()-]{8,30}$',max_length=30)
    agreed=forms.BooleanField(label='Tôi đã kiểm tra email, ngày sử dụng và đồng ý điều kiện của dịch vụ. Vé sẽ được nhân viên gửi qua email sau khi thanh toán.')
    website=forms.CharField(required=False,widget=forms.HiddenInput)
    def clean_visit_date(self):
        day=self.cleaned_data['visit_date'];today=timezone.localdate()
        if not today<=day<=today+timedelta(days=365):raise forms.ValidationError('Chọn ngày trong 365 ngày tới.')
        return day
    def clean_website(self):
        if self.cleaned_data['website']:raise forms.ValidationError('Không thể gửi yêu cầu.')
        return ''
