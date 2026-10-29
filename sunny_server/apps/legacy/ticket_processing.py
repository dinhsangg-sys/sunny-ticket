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
    # Keep line boundaries: OCR often places the value before the English label.
    lines=[line.strip() for line in text.splitlines() if line.strip() and not re.search(r'https?\s*:|www\.|invoiceid|is[_ ]agency|ticket[_ ]export|memoriesland[./?]',line,re.I)]
    text='\n'.join(lines)
    flat=unicodedata.normalize('NFC',re.sub(r'\s+',' ',text));norm=normalize(flat)
    def after(pattern):
        match=re.search(pattern,norm,re.I)
        return flat[match.end():].lstrip(' :') if match else ''
    def until(value,markers):
        positions=[m.start() for pattern in markers if (m:=re.search(pattern,normalize(value),re.I))]
        return value[:min(positions)].strip(' :') if positions else value.strip(' :')
    expiry=re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b',after(r'expiration\s*date') or flat)
    if not expiry:expiry=re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b',flat)
    package=until(after(r'service\s*package') or after(r'ten\s*goi\s*dich\s*vu'),[r'thoi gian',r'\btime\b',r'\bpark\b'])
    if package.lower().startswith('service'):package=until(re.sub(r'^service\s*package\s*:?\s*','',package,flags=re.I),[r'thoi gian',r'\btime\b',r'\bpark\b'])
    if not package:
        # Only accept a recognizable package printed on its own OCR line, never infer from booking.
        candidates=[line.strip() for line in text.splitlines() if re.fullmatch(r'\s*(?:ECO|HIGH|VIP)(?:[ -][A-Z0-9]+){0,5}\s*',line)]
        if len(candidates)==1:package=candidates[0]
    packages=re.findall(r'\b(?:ECO|HIGH|VIP)(?:[ -]+[A-Z0-9]+){0,5}\b',text)
    packages=[p.strip() for p in packages if not any(label in p for label in ('PARK','SHOW','TIME','CODE'))]
    if len(set(packages))==1:package=packages[0]
    park=re.search(r'P[A4]RK\s*:?\s*(\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2})',flat,re.I)
    show=re.search(r'SHOW\s*:?\s*(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2})',flat,re.I)
    code=re.search(r'\b\d{8,}(?:-\d+){1,4}\b',flat)
    agent=until(after(r'cooperative\s*agent') or after(r'dai\s*ly\s*hop\s*tac'),[r'https?://',r'\btrang\b',r'\d{1,2}/\d{1,2}/\d{2,4}'])
    agent=re.sub(r'^cooperative\s*agent\s*:?\s*','',agent,flags=re.I)
    agent=re.split(r'cooperative\s*agent',agent,flags=re.I)[0].strip(' :')
    def agent_value(value):
        value=value.strip(' :')
        return value if re.fullmatch(r'[A-Z][A-Z0-9_. -]{0,23}',value) and len(value.split())<=4 and not re.search(r'COOPERATIVE|AGENT|PARK|SHOW|SERVICE|PACKAGE',value) else ''
    # Prefer values on the same row as either language's label over later page text.
    for line in lines:
        normalized=normalize(line)
        for pattern in (r'dai\s*ly\s*hop\s*tac',r'cooperative\s*agent'):
            match=re.search(pattern,normalized)
            if match:
                value=re.split(r'cooperative\s*agent',line[match.end():],flags=re.I)[0].strip(' :')
                if agent_value(value):agent=value
    if not agent_value(agent):agent=''
    if not agent and code:
        # Value-only OCR crop: take a standalone code following the printed ticket code.
        following=False
        for line in lines:
            if code.group(0) in line:following=True;continue
            if following and agent_value(line):agent=line;break
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

def image_fields(image,column=False):
    if column:
        try:
            import pytesseract
            fields=text_fields(pytesseract.image_to_string(image,lang='vie+eng',config='--psm 6',timeout=30))
        except Exception:fields=text_fields('')
    else:fields=text_fields(ocr(image))
    if all(fields.values()):return fields
    # Retry a larger view of the text region; the dark artwork can dominate full-image OCR.
    try:
        import pytesseract
        cropped=image.crop((0,int(image.height*.58),image.width,image.height))
        width=min(2200,max(cropped.width,1600))
        cropped=ImageOps.autocontrast(cropped.convert('L').resize((width,round(cropped.height*width/cropped.width))))
        retry=text_fields(pytesseract.image_to_string(cropped,lang='vie+eng',config='--psm 6',timeout=30))
        for key in FIELDS:
            if not fields[key]:fields[key]=retry[key]
    except Exception:pass
    return fields

def qr_bounds(code):
    points=[code.position.top_left,code.position.top_right,code.position.bottom_left,code.position.bottom_right]
    return (min(p.x for p in points),min(p.y for p in points),max(p.x for p in points),max(p.y for p in points))


def ticket_regions(image,codes):
    """Split on visible paper gutters, never assign a whole page's text to multiple QRs."""
    if not codes:raise ValueError('Không đọc được QR. Dùng ảnh rõ hơn hoặc PDF gốc.')
    if len(codes)>50:raise ValueError('Tối đa 50 vé trong một đợt nhập.')
    gray=image.convert('L');width,height=image.size
    def split(box,group):
        if len(group)==1:return [(box,group[0])]
        candidates=[]
        for axis in (0,1):
            ordered=sorted(group,key=lambda c:qr_bounds(c)[axis])
            for index in range(1,len(ordered)):
                first,second=ordered[:index],ordered[index:]
                end=max(qr_bounds(c)[axis+2] for c in first);start=min(qr_bounds(c)[axis] for c in second)
                if start-end<8:continue
                # Search the full row/column so gaps inside the information panel do not cut artwork.
                runs=[];begin=None
                for pos in range(int(end)+2,int(start)-2):
                    line=gray.crop((box[0],pos,box[2],pos+1) if axis==1 else (pos,box[1],pos+1,box[3]))
                    histogram=line.histogram();blank=sum(histogram[:238])<=line.width*line.height*.012
                    if blank and begin is None:begin=pos
                    if not blank and begin is not None:runs.append((begin,pos));begin=None
                if begin is not None:runs.append((begin,int(start)-2))
                runs=[r for r in runs if r[1]-r[0]>=max(3,(height if axis else width)*.002)]
                if runs:
                    run=max(runs,key=lambda r:r[1]-r[0]);candidates.append((float(run[1]-run[0])/(height if axis else width),axis,(run[0]+run[1])//2,first,second))
        if not candidates:raise ValueError('Có nhiều QR nhưng không tách rõ vùng từng vé. Hãy cắt từng vé hoặc dùng PDF có khoảng trắng giữa các vé.')
        _,axis,cut,first,second=max(candidates,key=lambda c:c[0])
        left=list(box);right=list(box);left[axis+2]=cut;right[axis]=cut
        return split(tuple(left),first)+split(tuple(right),second)
    return sorted(split((0,0,width,height),codes),key=lambda pair:(pair[0][1],pair[0][0]))


def region_fields(image):
    # Horizontal ticket artwork is on the left in the supplied layout. Restrict OCR to its
    # information panel only when the QR is clearly on the right; do not infer field values.
    codes=decode(image)
    if len(codes)==1:
        left,top,right,bottom=qr_bounds(codes[0])
        if (left+right)/2>image.width*.60:
            # This layout prints a value column beneath the right-hand QR. Exclude bilingual
            # labels and cap the bottom using QR size so the browser footer never enters OCR.
            width=right-left;height=bottom-top
            values=image.crop((max(0,int(left-width*.12)),max(0,int(bottom+height*.15)),min(image.width,int(right+width*2.1)),min(image.height,int(bottom+height*2.9))))
            values=ImageOps.autocontrast(values.convert('L'))
            target=min(1800,max(values.width,1400))
            values=values.resize((target,round(values.height*target/values.width)))
            fields=image_fields(values,column=True)
            return fields
    return image_fields(image)


def extract_tickets(blob):
    result=[];seen=set()
    def append(image,page_number,page=None,scale=1):
        codes=decode(image)
        for region,code in ticket_regions(image,codes):
            png,digest=qr_from(image,code)
            if digest in seen:raise ValueError('QR trùng trong file; chưa nhập bộ vé.')
            seen.add(digest)
            if len(result)>=50:raise ValueError('Tối đa 50 vé trong một đợt nhập.')
            crop=image.crop(region)
            text=page.get_text('text',clip=fitz.Rect(*(v/scale for v in region))) if page is not None else ''
            fields=text_fields(text) if text.strip() else region_fields(crop)
            result.append({'page':len(result)+1,'source_page':page_number,'source_region':list(region),**fields,'qr_hash':digest,'qr_png':png})
    if blob.startswith(b'%PDF-'):
        with fitz.open(stream=blob,filetype='pdf') as document:
            if document.needs_pass or not 1<=len(document)<=50:raise ValueError('PDF phải mở được và có từ 1 đến 50 trang.')
            for index,page in enumerate(document):
                if page.rect.width*page.rect.height>2000000:raise ValueError('Khổ trang PDF quá lớn.')
                pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
                image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
                append(image,index+1,page,2)
    else:
        with Image.open(BytesIO(blob)) as original:
            if original.format not in ('JPEG','PNG') or original.width*original.height>25000000:raise ValueError('Chỉ hỗ trợ PDF, JPEG/PNG, tối đa 25 triệu điểm ảnh.')
            append(ImageOps.exif_transpose(original).convert('RGB'),1)
    return result

def checked_fields(row):
    fields={key:row.get(key,'').strip() if isinstance(row.get(key,''),str) else '' for key in FIELDS}
    labels={'expiry':'Hạn sử dụng','package':'Gói dịch vụ','park_time':'Giờ PARK','show_time':'Giờ SHOW','ticket_code':'Mã vé gốc','agent':'Đại lý gốc'}
    missing=[labels[k] for k,v in fields.items() if not v]
    if missing:raise ValueError('Chưa đọc/điền đủ: '+', '.join(missing)+'. Điền theo vé gốc rồi tạo PDF; không cần import lại.')
    if any(len(v)>120 or any(ord(c)<32 for c in v) for v in fields.values()):raise ValueError('Mỗi trường tối đa 120 ký tự, không xuống dòng.')
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
        if len(check)!=len(rows):raise ValueError('Số trang PDF không khớp số vé đã chọn; chưa xuất vé.')
        for page,row in zip(check,rows):
            pix=page.get_pixmap(matrix=fitz.Matrix(4,4),alpha=False);image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
            hashes=[hashlib.sha256(b.bytes).hexdigest() for b in decode(image)]
            if hashes!=[row['qr_hash']]:raise ValueError('QR trên PDF đầu ra không khớp vé gốc; chưa xuất vé.')
    return blob
