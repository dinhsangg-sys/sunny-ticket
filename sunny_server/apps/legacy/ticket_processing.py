"""Local-only ticket extraction/rendering. QR images are copied, never regenerated."""
from datetime import datetime
from io import BytesIO
from pathlib import Path
import hashlib
import re
import unicodedata
import pymupdf as fitz
from PIL import Image, ImageOps
import zxingcpp
from django.conf import settings

FIELDS=('expiry','package','park_time','show_time','ticket_code','agent')

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD',value.lower()) if unicodedata.category(c)!='Mn').replace('đ','d')

def text_fields(text):
    flat=unicodedata.normalize('NFC',re.sub(r'\s+',' ',text));norm=normalize(flat)
    def after(pattern):
        match=re.search(pattern,norm,re.I)
        return flat[match.end():].lstrip(' :') if match else ''
    def until(value,markers):
        positions=[m.start() for pattern in markers if (m:=re.search(pattern,normalize(value),re.I))]
        return value[:min(positions)].strip(' :') if positions else value.strip(' :')
    expiry=re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b',after(r'expiration\s*date') or flat)
    package=until(after(r'service\s*package'),[r'thoi gian',r'\btime\b',r'\bpark\b'])
    park=re.search(r'PARK\s*:?\s*(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2})',flat,re.I)
    show=re.search(r'SHOW\s*:?\s*(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2})',flat,re.I)
    code=re.search(r'\b\d{8,}(?:-\d+){1,4}\b',flat)
    agent=until(after(r'cooperative\s*agent'),[r'https?://',r'\btrang\b',r'\d{1,2}/\d{1,2}/\d{2,4}'])
    return {'expiry':expiry.group(0) if expiry else '', 'package':package[:100], 'park_time':park.group(1) if park else '', 'show_time':show.group(1) if show else '', 'ticket_code':code.group(0) if code else '', 'agent':agent[:60]}

def decode(image):
    return [b for b in zxingcpp.read_barcodes(image) if b.format==zxingcpp.BarcodeFormat.QRCode and b.valid]

def qr_from(image,barcode,whole=False):
    if not whole:
        points=[barcode.position.top_left,barcode.position.top_right,barcode.position.bottom_left,barcode.position.bottom_right]
        left=min(p.x for p in points);top=min(p.y for p in points);right=max(p.x for p in points);bottom=max(p.y for p in points)
        pad=max(10,round(max(right-left,bottom-top)*.15))
        image=image.crop((max(0,left-pad),max(0,top-pad),min(image.width,right+pad),min(image.height,bottom+pad)))
    image=image.convert('RGB');stream=BytesIO();image.save(stream,format='PNG')
    if barcode.bytes not in [b.bytes for b in decode(image)]:raise ValueError('Không xác minh được ảnh QR sau khi tách.')
    return stream.getvalue(),hashlib.sha256(barcode.bytes).hexdigest()

def ocr(image):
    try:
        import pytesseract
        return pytesseract.image_to_string(image,lang='vie+eng',timeout=30)
    except Exception:
        return ''

def extract_tickets(blob):
    result=[];seen=set()
    if blob.startswith(b'%PDF-'):
        document=fitz.open(stream=blob,filetype='pdf')
        if document.needs_pass or not 1<=len(document)<=50:raise ValueError('PDF phải mở được và có từ 1 đến 50 trang.')
        for index,page in enumerate(document):
            found=[]
            for reference in page.get_images(full=True):
                raw=document.extract_image(reference[0])['image']
                with Image.open(BytesIO(raw)) as image:
                    if image.width*image.height>25000000:raise ValueError('Ảnh trong PDF quá lớn.')
                    for code in decode(image):found.append(qr_from(image,code))
            text=page.get_text('text')
            if not found or not text.strip():
                if page.rect.width*page.rect.height>2000000:raise ValueError('Khổ trang PDF quá lớn.')
                pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False);image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
                if not found:found=[qr_from(image,b) for b in decode(image)]
                if not text.strip():text=ocr(image)
            unique={digest:png for png,digest in found}
            if len(unique)!=1:raise ValueError(f'Trang {index+1}: cần đúng một QR đọc được. Hãy tách trang có nhiều QR hoặc dùng ảnh rõ hơn.')
            digest,png=next(iter(unique.items()))
            if digest in seen:raise ValueError(f'Trang {index+1}: QR trùng trang trước, chưa nhập file.')
            seen.add(digest);result.append({'page':index+1,**text_fields(text),'qr_hash':digest,'qr_png':png})
        document.close()
    else:
        with Image.open(BytesIO(blob)) as image:
            if image.format not in ('JPEG','PNG') or image.width*image.height>25000000:raise ValueError('Chỉ hỗ trợ PDF, JPEG/PNG, tối đa 25 triệu điểm ảnh.')
            image=ImageOps.exif_transpose(image).convert('RGB');codes=decode(image)
            if len(codes)!=1:raise ValueError('Ảnh cần đúng một mã QR đọc được. Hãy chụp rõ hoặc tách từng vé.')
            png,digest=qr_from(image,codes[0]);result=[{'page':1,**text_fields(ocr(image)),'qr_hash':digest,'qr_png':png}]
    return result

def checked_fields(row):
    fields={key:row.get(key,'').strip() if isinstance(row.get(key,''),str) else '' for key in FIELDS}
    if any(not v or len(v)>120 or any(ord(c)<32 for c in v) for v in fields.values()):raise ValueError('Điền đủ thông tin từng vé, mỗi trường tối đa 120 ký tự, không xuống dòng.')
    try:datetime.strptime(fields['expiry'],'%d/%m/%Y')
    except ValueError:raise ValueError('Hạn sử dụng phải là DD/MM/YYYY.')
    for key in ('park_time','show_time'):
        if not re.fullmatch(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}',fields[key]):raise ValueError('Giờ PARK/SHOW cần dạng HH:MM - HH:MM.')
        try:
            for value in re.split(r'[-–]',fields[key]):datetime.strptime(value.strip(),'%H:%M')
        except ValueError:raise ValueError('Giờ PARK/SHOW chưa hợp lệ.')
    return fields

def render_tickets(rows,qr_files):
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    font=getattr(settings,'COUNTER_TICKET_FONT','')
    options=[font,'/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf']
    path=next((p for p in options if p and Path(p).is_file()),None)
    if not path:raise ValueError('Chưa có font in vé. Quản trị cần cài fonts-dejavu-core hoặc cấu hình COUNTER_TICKET_FONT.')
    if 'CounterTicket' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('CounterTicket',path))
    template=fitz.open(Path(settings.BASE_DIR)/'ticket_templates'/'counter_80x110.pdf')
    output=fitz.open();height=110*mm
    positions={'expiry':(25,75.2,52,8),'package':(25,82.6,52,8),'park_time':(25,89.4,52,7.7),'show_time':(25,93,52,7.7),'ticket_code':(25,98,52,7.4),'agent':(25,104.3,52,8)}
    for row,png in zip(rows,qr_files):
        stream=BytesIO();c=canvas.Canvas(stream,pagesize=(80*mm,height));c.drawImage(ImageReader(BytesIO(png)),31*mm,height-67.5*mm,width=18*mm,height=18*mm,preserveAspectRatio=True,anchor='c')
        for key,(x,y,width,size) in positions.items():
            text=row[key]
            if key=='park_time':text='PARK: '+text
            if key=='show_time':text='SHOW: '+text
            while pdfmetrics.stringWidth(text,'CounterTicket',size)>width*mm and size>5.5:size-=.1
            if pdfmetrics.stringWidth(text,'CounterTicket',size)>width*mm:raise ValueError('Thông tin quá dài để vừa mẫu vé: '+key)
            c.setFont('CounterTicket',size);c.drawString(x*mm,height-y*mm,text)
        c.showPage();c.save();overlay=fitz.open(stream=stream.getvalue(),filetype='pdf')
        page=output.new_page(width=80*mm,height=height);page.show_pdf_page(page.rect,template,0);page.show_pdf_page(page.rect,overlay,0)
        overlay.close()
    blob=output.tobytes(garbage=3,deflate=True);output.close();template.close()
    with fitz.open(stream=blob,filetype='pdf') as check:
        for page,row in zip(check,rows):
            pix=page.get_pixmap(matrix=fitz.Matrix(4,4),alpha=False);image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
            hashes=[hashlib.sha256(b.bytes).hexdigest() for b in decode(image)]
            if hashes!=[row['qr_hash']]:raise ValueError('QR trên PDF đầu ra không khớp vé gốc; chưa xuất vé.')
    return blob
