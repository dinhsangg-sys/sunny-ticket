"""Permission names are stable; role alone never grants workspace write access."""
def codename(name): return name.replace('.','__')
def allowed(user,name):
    return user.is_active and (user.is_superuser or user.has_perm('legacy.'+codename(name)))
def full_access(user): return allowed(user,'workspace.full_access')

# Fields accepted by the restricted editor. Derived/financial fields cannot be injected.
RESOURCES = {
 'cashTransactions':('cashbook','Thu chi thủ công',{'id':'Mã','date':'Ngày','kind':'Loại (capital/income/expense)','category':'Nhóm','amount':'Số tiền','note':'Ghi chú'}),
 'zaloCampaigns':('crm','Chiến dịch Zalo',{'id':'Mã','title':'Tên chiến dịch','body':'Nội dung'}),
 'ticketTypes':('ticket_type','Loại vé',{'id':'Mã','name':'Tên','product':'Sản phẩm','active':'Đang dùng','sortOrder':'Thứ tự'}),
 'agents':('agency','Đại lý',{'id':'Mã','name':'Tên','phone':'Điện thoại','email':'Email','note':'Ghi chú','active':'Hoạt động','priceListId':'Bảng giá','zaloLink':'Link Zalo'}),
 'suppliers':('supplier','Nhà cung cấp',{'id':'Mã','name':'Tên','phone':'Điện thoại','active':'Hoạt động'}),
 'priceLists':('price_list','Bảng giá dùng chung',{'id':'Mã','name':'Tên','active':'Hoạt động'}),
 'priceListItems':('price_list_item','Giá trong bảng chung',{'id':'Mã dòng','priceListId':'Bảng giá','ticketId':'Loại vé','price':'Giá bán','from':'Từ ngày','to':'Đến ngày'}),
 'agentPrices':('agency_price','Giá riêng đại lý',{'id':'Mã dòng','agent':'Tên đại lý','ticketId':'Loại vé','price':'Giá bán','from':'Từ ngày','to':'Đến ngày'}),
 'costPrices':('cost_price','Giá vốn',{'id':'Mã dòng','supplierId':'Nhà cung cấp','ticketId':'Loại vé','price':'Giá vốn','from':'Từ ngày','to':'Đến ngày','isDefault':'Mặc định'}),
 'expenses':('expense_template','Mẫu chi phí',{'id':'Mã dòng','date':'Ngày','title':'Nội dung','amount':'Số tiền','note':'Ghi chú'}),
 'bookings':('booking','Booking',{'id':'Mã','date':'Ngày','customerType':'Loại khách','agent':'Tên đại lý','customerName':'Khách lẻ','ticketId':'Loại vé','supplierId':'Nhà cung cấp','qty':'Số lượng','sellPrice':'Giá bán','buyPrice':'Giá vốn','cost':'Chi phí','hasVat':'VAT','vatRate':'Thuế suất','note':'Ghi chú'}),
}
NUMBERS={'price','amount','qty','sellPrice','buyPrice','cost','vatRate','sortOrder'}
BOOLS={'active','isDefault','hasVat'}

def field_permission(resource,field):
    return {
      ('ticketTypes','active'):'ticket_type.change_status',('ticketTypes','sortOrder'):'ticket_type.reorder',
      ('agents','active'):'agency.change_status',('agents','zaloLink'):'agency.change_zalo_link',
      ('agents','priceListId'):'agency.assign_price_list',('costPrices','isDefault'):'cost_price.set_default',
      ('bookings','sellPrice'):'booking.change_sell_price',('bookings','buyPrice'):'booking.change_buy_price',
      ('bookings','cost'):'booking.change_expense',('bookings','hasVat'):'booking.change_vat',('bookings','vatRate'):'booking.change_vat',
    }.get((resource,field))

def can_field(user,resource,field):
    p=field_permission(resource,field)
    return full_access(user) or not p or allowed(user,p)

def projected(user,key,row):
    result=dict(row)
    if full_access(user): return result
    if key=='zaloCampaigns' and not allowed(user,'crm.view_recipients'): result.pop('recipients',None)
    if key=='agents' and not allowed(user,'agency.view_contact'):
        for f in ('phone','email','zaloLink'): result.pop(f,None)
    if key=='bookings':
        if not allowed(user,'booking.view_buy_price'):
            for f in ('buyPrice','costPriceId','vatBase','vatAmount'): result.pop(f,None)
        if not allowed(user,'booking.view_profit'): result.pop('profit',None)
        if not allowed(user,'receipt.view'): result.pop('payments',None)
        if not allowed(user,'supplier_payment.view'): result.pop('supplierPayments',None)
    return result

def action_permission(resource,action,kind=None):
    if resource=='cashTransactions':
        return {'capital':'capital','income':'other_income','expense':'other_expense'}.get(kind,'invalid')+'.'+action
    if resource=='zaloCampaigns': return {'create':'crm.create_campaign','change':'crm.change_campaign','delete':'unsupported.delete_campaign'}.get(action,'crm.view')
    return RESOURCES[resource][0]+'.'+action
