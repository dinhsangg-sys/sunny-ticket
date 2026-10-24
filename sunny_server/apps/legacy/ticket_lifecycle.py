"""Keep identifiers and historical ticket references intact across both APIs."""
REFERENCES = ('bookings','agentPrices','costPrices','priceListItems')

def ticket_used(data,ticket):
    if ticket.get('hasActivity'): return True
    for collection in REFERENCES:
        for row in data.get(collection,[]):
            explicit=[row.get(k) for k in ('ticketId','ticketCode') if row.get(k)]
            if explicit:
                if ticket['id'] in explicit: return True
            elif row.get('ticketType') and row['ticketType'] in (ticket['id'],ticket.get('name')):
                return True
    return False

def enforce_ticket_lifecycle(before,after):
    old={t['id']:t for t in before.get('ticketTypes',[])}
    new={t['id']:t for t in after.get('ticketTypes',[])}
    for key,ticket in old.items():
        if key not in new and (ticket_used(before,ticket) or ticket_used(after,ticket)):
            raise ValueError('Loại vé '+str(ticket.get('name',key))+' đã phát sinh dữ liệu; chỉ được dừng sử dụng, không được xóa.')
    for key,ticket in new.items():
        ticket['hasActivity']=bool(ticket_used(after,ticket) or key in old and ticket_used(before,old[key]))
