import re
from django import forms

# Shared calling codes (US/Canada) remain separate country choices.
COUNTRIES=[('US','United States','Mỹ','1'),('CA','Canada','Canada','1'),('VN','Vietnam','Việt Nam','84'),('GB','United Kingdom','Anh','44'),('AU','Australia','Úc','61'),('NZ','New Zealand','New Zealand','64'),('CN','China','Trung Quốc','86'),('JP','Japan','Nhật Bản','81'),('KR','South Korea','Hàn Quốc','82'),('TW','Taiwan','Đài Loan','886'),('HK','Hong Kong','Hồng Kông','852'),('SG','Singapore','Singapore','65'),('TH','Thailand','Thái Lan','66'),('MY','Malaysia','Malaysia','60'),('ID','Indonesia','Indonesia','62'),('PH','Philippines','Philippines','63'),('IN','India','Ấn Độ','91'),('FR','France','Pháp','33'),('DE','Germany','Đức','49'),('IT','Italy','Ý','39'),('ES','Spain','Tây Ban Nha','34'),('PT','Portugal','Bồ Đào Nha','351'),('NL','Netherlands','Hà Lan','31'),('BE','Belgium','Bỉ','32'),('CH','Switzerland','Thụy Sĩ','41'),('AT','Austria','Áo','43'),('IE','Ireland','Ireland','353'),('SE','Sweden','Thụy Điển','46'),('NO','Norway','Na Uy','47'),('DK','Denmark','Đan Mạch','45'),('FI','Finland','Phần Lan','358'),('PL','Poland','Ba Lan','48'),('CZ','Czechia','Séc','420'),('RU','Russia','Nga','7'),('TR','Türkiye','Thổ Nhĩ Kỳ','90'),('AE','United Arab Emirates','UAE','971'),('SA','Saudi Arabia','Ả Rập Xê Út','966'),('IL','Israel','Israel','972'),('ZA','South Africa','Nam Phi','27'),('BR','Brazil','Brazil','55'),('MX','Mexico','Mexico','52'),('AR','Argentina','Argentina','54'),('CL','Chile','Chile','56'),('KH','Cambodia','Campuchia','855'),('LA','Laos','Lào','856'),('MM','Myanmar','Myanmar','95'),('BD','Bangladesh','Bangladesh','880'),('PK','Pakistan','Pakistan','92'),('NP','Nepal','Nepal','977'),('LK','Sri Lanka','Sri Lanka','94'),('MN','Mongolia','Mông Cổ','976')]

def country(value):
    value=(value or '+1').strip().casefold()
    for iso,en,vi,code in COUNTRIES:
        if value in {iso.casefold(),en.casefold(),vi.casefold(),'+'+code,(en+' (+'+code+')').casefold(),(vi+' (+'+code+')').casefold()}:return iso,code
    raise forms.ValidationError('Chọn quốc gia hoặc nhập mã hợp lệ, ví dụ +84 / Choose a country or valid code, e.g. +1.')

def normalize_phone(raw,country_value):
    iso,code=country(country_value)
    raw=(raw or '').strip()
    if not re.fullmatch(r'[+0-9 ()-]+',raw):raise forms.ValidationError('Số điện thoại không hợp lệ. / Invalid phone number.')
    digits=re.sub(r'[ ()-]','',raw)
    if digits.startswith('00'):digits='+'+digits[2:]
    if digits.startswith('+'):
        if not digits[1:].isdigit() or not digits[1:].startswith(code):raise forms.ValidationError('Số điện thoại không khớp mã quốc gia đã chọn. / Phone number does not match the selected calling code.')
        national=digits[1+len(code):]
    else:
        national=digits
    if iso!='IT':national=national.lstrip('0')
    if iso in {'US','CA'} and (len(national)!=10 or national[0] not in '23456789'):raise forms.ValidationError('Số +1 cần 10 chữ số, không gồm mã quốc gia. / A +1 number needs 10 digits excluding the calling code.')
    if iso=='VN' and len(national) not in (9,10):raise forms.ValidationError('Kiểm tra số điện thoại Việt Nam. / Check the Vietnamese phone number.')
    result='+'+code+national
    if not national.isdigit() or not 6<=len(national) or not 8<=len(result)-1<=15:raise forms.ValidationError('Kiểm tra lại số điện thoại (tối đa 15 chữ số gồm mã quốc gia). / Check the phone number (up to 15 digits including calling code).')
    return result

class CountryWidget(forms.TextInput):
    template_name='online/widgets/phone_country.html'
    lang='en'
    class Media:
        css={'all':('css/phone_country.css',)}
        js=('js/phone_country.js',)
    def get_context(self,name,value,attrs):
        context=super().get_context(name,value,attrs)
        context['widget']['countries']=[{'value':(en if self.lang=='en' else vi)+' (+'+code+')','search':iso+' '+en+' '+vi+' +'+code} for iso,en,vi,code in COUNTRIES]
        context['widget']['toggle']='Choose country' if self.lang=='en' else 'Chọn quốc gia'
        return context
