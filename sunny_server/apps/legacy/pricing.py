"""Pricing rules shared by compatibility UI and permission-restricted API."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlsplit
from datetime import date as calendar_date
import re

COLLECTIONS = ('ticketTypes','agents','agentPrices','costPrices','bookings','expenses','cashTransactions','zaloCampaigns','suppliers','priceLists','priceListItems','ticketMappings')

def amount(value):
    try:
        result=Decimal(str(value))
        if not result.is_finite() or result < 0: raise ValueError('Số tiền phải không âm và hữu hạn.')
        if result>Decimal('1000000000000000'): raise ValueError('Số tiền vượt giới hạn cho phép.')
        return result
    except (InvalidOperation,TypeError): raise ValueError('Số tiền không hợp lệ.')

def valid_zalo_link(value):
    if not value: return True
    try:
        p=urlsplit(value)
        return p.scheme=='https' and p.hostname=='zalo.me' and not p.username and not p.password and p.port in (None,443) and bool(p.path.strip('/')) and not any(c.isspace() for c in value)
    except ValueError: return False

def mapping(data, ticket_id):
    return next((x for x in data.get('ticketMappings',[]) if x.get('legacyId')==ticket_id),None)

def canonical(data, ticket_id):
    m=mapping(data,ticket_id)
    return m['ticketId'] if m else ticket_id

def row_ticket(data,row):
    key=row.get('ticketId') or row.get('ticketCode')
    if not key:
        key=next((t['id'] for t in data.get('ticketTypes',[]) if t.get('name')==row.get('ticketType')),None)
    return canonical(data,key)

def effective(row,date):
    return (row.get('from') or '0001-01-01')<=date and (not row.get('to') or row['to']>=date)

def unique_price(rows):
    values={amount(r['price']) for r in rows}
    if len(values)>1: raise ValueError('Có nhiều giá khác nhau cùng hiệu lực. Cần đối soát bảng giá.')
    return float(next(iter(values))) if values else None

def sell_price(data,agency_id,ticket_id,date):
    agency=next((a for a in data.get('agents',[]) if a['id']==agency_id),None)
    if not agency: raise ValueError('Không tìm thấy đại lý.')
    tid=canonical(data,ticket_id)
    own=[p for p in data.get('agentPrices',[]) if p.get('agent')==agency['name'] and row_ticket(data,p)==tid and effective(p,date)]
    if own: return unique_price(own),'Giá riêng đại lý'
    group=next((p for p in data.get('priceLists',[]) if p['id']==agency.get('priceListId') and p.get('active',True)),None)
    if not group: return None,'Chưa gán bảng giá / chưa có giá riêng'
    rows=[p for p in data.get('priceListItems',[]) if p.get('priceListId')==group['id'] and row_ticket(data,p)==tid and effective(p,date)]
    return unique_price(rows),group['name']

def supplier_options(data,ticket_id,date):
    tid=canonical(data,ticket_id)
    result=[]
    for p in data.get('costPrices',[]):
        if row_ticket(data,p)!=tid or not effective(p,date): continue
        m=mapping(data,p.get('ticketId') or p.get('ticketCode'))
        supplier_id=p.get('supplierId') or (m or {}).get('supplierId','')
        supplier=next((s for s in data.get('suppliers',[]) if s['id']==supplier_id and s.get('active',True)),None)
        if not supplier: continue
        result.append(dict(p,supplierId=supplier_id,supplierName=supplier['name']))
    # Distinct suppliers must remain distinct even if amounts match.
    return result

def validate(data):
    if not isinstance(data,dict): raise ValueError('Dữ liệu phải là object.')
    for key in COLLECTIONS:
        rows=data.get(key,[])
        if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows): raise ValueError('Danh sách không hợp lệ: '+key)
    for key in ('ticketTypes','agents','suppliers','priceLists'):
        rows=data.get(key,[])
        ids=[r.get('id') for r in rows]
        if any(not isinstance(i,str) or not i for i in ids) or len(ids)!=len(set(ids)): raise ValueError('Mã thiếu hoặc trùng: '+key)
        if key in ('suppliers','priceLists') and any(not re.fullmatch(r'[A-Za-z0-9_.-]{1,120}',i) for i in ids): raise ValueError('Mã nhà cung cấp/bảng giá chỉ gồm chữ không dấu, số, dấu gạch ngang, gạch dưới hoặc chấm.')
    for a in data.get('agents',[]):
        if not valid_zalo_link(a.get('zaloLink','')): raise ValueError('Link Zalo chỉ được dùng https://zalo.me/...')
        if a.get('priceListId') and not any(p['id']==a['priceListId'] for p in data.get('priceLists',[])): raise ValueError('Bảng giá đại lý không tồn tại.')
    for key in ('agentPrices','costPrices','priceListItems'):
        for p in data.get(key,[]):
            amount(p.get('price',0))
            for field in ('from','to'):
                if p.get(field): calendar_date.fromisoformat(p[field])
            if p.get('to') and p.get('from') and p['to']<p['from']: raise ValueError('Khoảng ngày không hợp lệ.')
    ids={t['id'] for t in data.get('ticketTypes',[])}
    suppliers={s['id'] for s in data.get('suppliers',[])}
    for p in data.get('costPrices',[]):
        if p.get('supplierId') and p['supplierId'] not in suppliers: raise ValueError('Nhà cung cấp không tồn tại.')
    for p in data.get('priceListItems',[]):
        if not isinstance(p.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,120}',p['id']): raise ValueError('Mã dòng bảng giá không hợp lệ.')
        if p.get('ticketId') not in ids or not any(g['id']==p.get('priceListId') for g in data.get('priceLists',[])): raise ValueError('Bảng giá hoặc loại vé không tồn tại.')
    for key in ('suppliers','priceLists'):
        if any(not r.get('name','').strip() for r in data.get(key,[])): raise ValueError('Thiếu tên '+key)
    for i,p in enumerate(data.get('costPrices',[])):
        if not p.get('supplierId'): continue  # Keep legacy records untouched until explicitly mapped.
        for q in data.get('costPrices',[])[i+1:]:
            if q.get('supplierId')==p['supplierId'] and row_ticket(data,p)==row_ticket(data,q) and (p.get('from') or '')<=(q.get('to') or '9999') and (q.get('from') or '')<=(p.get('to') or '9999') and amount(p['price'])!=amount(q['price']): raise ValueError('Giá vốn cùng nhà cung cấp trùng hiệu lực.')
    mapped=set()
    for m in data.get('ticketMappings',[]):
        if m.get('legacyId') not in ids or m.get('ticketId') not in ids or m['legacyId']==m['ticketId'] or m.get('supplierId') not in suppliers: raise ValueError('Ánh xạ vé/nhà cung cấp không hợp lệ.')
        if m['legacyId'] in mapped: raise ValueError('Loại vé cũ bị ánh xạ nhiều lần.')
        mapped.add(m['legacyId'])
    if any(m['ticketId'] in mapped for m in data.get('ticketMappings',[])): raise ValueError('Không được ánh xạ nối chuỗi.')
    # Reject newly ambiguous sale prices instead of choosing an arbitrary supplier price.
    for key,owner in [('agentPrices','agent'),('priceListItems','priceListId')]:
        rows=data.get(key,[])
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                if a.get(owner)==b.get(owner) and row_ticket(data,a)==row_ticket(data,b) and (a.get('from') or '')<=(b.get('to') or '9999') and (b.get('from') or '')<=(a.get('to') or '9999') and amount(a['price'])!=amount(b['price']):
                    raise ValueError('Giá bán trùng hiệu lực nhưng khác số tiền. Cần đối soát trước khi gộp.')

def calculate_booking(row):
    qty=amount(row.get('qty',0))
    if qty<=0 or qty!=qty.to_integral_value(): raise ValueError('Số lượng phải là số nguyên dương.')
    buy,sell,cost=amount(row.get('buyPrice',0)),amount(row.get('sellPrice',0)),amount(row.get('cost',0))
    rate=amount(row.get('vatRate',0)) if row.get('hasVat') else Decimal(0)
    if rate>100: raise ValueError('Thuế suất không hợp lệ.')
    base=max(Decimal(0),(sell-buy)*qty)
    vat=(base*rate/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)
    revenue=sell*qty-cost
    if revenue<0: raise ValueError('Chi phí lớn hơn tổng giá bán.')
    row.update(revenue=float(revenue),profit=float(revenue-buy*qty-vat),vatBase=float(base),vatAmount=float(vat))
    if sum(amount(p['amount']) for p in row.get('payments',[]))>revenue: raise ValueError('Tổng thu vượt doanh thu booking.')
    if sum(amount(p['amount']) for p in row.get('supplierPayments',[]))>buy*qty: raise ValueError('Tổng chi vượt giá vốn booking.')
    return row
