"""Keep the online purchase and bank receipt immutable in ordinary workspace editors."""
def protect_online_bookings(before,after):
    originals={b.get('id'):b for b in before.get('bookings',[]) if b.get('salesChannel')=='online'}
    fields=('bookingCode','date','ticketId','ticketType','product','qty','sellPrice','buyPrice','cost','supplierId','costPriceId','supplierName','payments','salesChannel','agent','customerEmail')
    for row in after.get('bookings',[]):
        old=originals.get(row.get('id'))
        if old and any(row.get(key)!=old.get(key) for key in fields):
            raise ValueError('Đơn online đã thu tiền: không sửa giá, số lượng, ngày, loại vé, email hoặc khoản thu trực tiếp; cần quản trị đối soát. Có thể tiếp tục nhập và gửi vé.')
