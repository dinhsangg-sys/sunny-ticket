from pathlib import Path
from PIL import Image
from django import forms
from django.forms import inlineformset_factory
from .models import Product,Asset,Article

class ProductForm(forms.ModelForm):
    expected_version=forms.IntegerField(widget=forms.HiddenInput,required=False)
    class Meta:
        model=Product
        fields=['sku','name','name_en','category','category_en','summary','summary_en','story','story_en','price','cost','published','sort_order']
        widgets={'story':forms.Textarea(attrs={'rows':8}),'summary':forms.Textarea(attrs={'rows':3})}

class AssetForm(forms.ModelForm):
    class Meta:model=Asset;fields=['kind','file','caption','caption_en','position']
    def clean_file(self):
        file=self.cleaned_data.get('file')
        if not file or not hasattr(file,'content_type'):return file
        ext=Path(file.name).suffix.lower();kind=self.cleaned_data.get('kind')
        if kind=='image':
            if file.size>10*1024*1024:raise forms.ValidationError('Hình ảnh tối đa 10 MB.')
            try:
                image=Image.open(file)
                if ext not in {'JPEG':('.jpg','.jpeg'),'PNG':('.png',),'WEBP':('.webp',)}.get(image.format,()) or image.width*image.height>24000000:raise ValueError()
                image.verify()
            except Exception:raise forms.ValidationError('Dùng ảnh JPEG, PNG hoặc WebP hợp lệ, tối đa 24 megapixel.')
        elif kind=='video':
            if file.size>100*1024*1024:raise forms.ValidationError('Video tối đa 100 MB.')
            header=file.read(32)
            if not (ext=='.mp4' and header[4:8]==b'ftyp' or ext=='.webm' and header.startswith(b'\x1aE\xdf\xa3')):raise forms.ValidationError('Video cần là MP4 hoặc WebM hợp lệ.')
        file.seek(0);return file

Assets=inlineformset_factory(Product,Asset,form=AssetForm,extra=2,can_delete=True,max_num=30,validate_max=True)
Articles=inlineformset_factory(Product,Article,fields=['title','title_en','body','body_en','position'],extra=1,can_delete=True,max_num=30,validate_max=True,widgets={'body':forms.Textarea(attrs={'rows':6})})
