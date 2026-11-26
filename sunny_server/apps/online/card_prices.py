from datetime import date,timedelta
from django.db.models import Q
from django.utils import timezone
from apps.legacy.models import Workspace
from apps.legacy.counter import default_cost
from .models import OnlinePrice


def attach_card_prices(services):
    """Show an actual purchasable starting price, never a manually invented amount."""
    services=list(services)
    if not services:return services
    today=timezone.localdate();last=today+timedelta(days=365)
    data=Workspace.objects.filter(pk=1).values_list('data',flat=True).first() or {}
    rows=list(OnlinePrice.objects.filter(service_id__in=[s.pk for s in services],active=True,starts_on__lte=last).filter(Q(ends_on__isnull=True)|Q(ends_on__gte=today)).select_related('option').order_by('price','starts_on','pk'))
    for service in services:
        service.card_price=None;service.card_ticket_title='';service.card_ticket_title_en=''
        if service.card_price_source=='option' and not service.card_price_option_id:continue
        candidates=[]
        for price in rows:
            if price.service_id!=service.pk or not 0<price.price<=100000000:continue
            option=price.option
            if option and (not option.active or option.service_id!=service.pk):continue
            if service.card_price_source=='default' and option is not None:continue
            if service.card_price_source=='option' and price.option_id!=service.card_price_option_id:continue
            ticket_id=option.ticket_id if option else service.ticket_id
            if len([t for t in data.get('ticketTypes',[]) if t.get('id')==ticket_id and t.get('active',True)])!=1:continue
            candidates.append((price,option,ticket_id))
        for price,option,ticket_id in candidates:
            start=max(today,price.starts_on);end=min(last,price.ends_on or last)
            peers=[p for p in rows if p.service_id==service.pk and p.option_id==price.option_id]
            days={start}
            for peer in peers:
                if peer.ends_on and start<=peer.ends_on+timedelta(days=1)<=end:days.add(peer.ends_on+timedelta(days=1))
            for cost in data.get('costPrices',[]):
                if cost.get('ticketId')!=ticket_id:continue
                for field in ('from','to'):
                    try:boundary=date.fromisoformat(cost.get(field,''))+(timedelta(days=1) if field=='to' else timedelta())
                    except (ValueError,TypeError):continue
                    if start<=boundary<=end:days.add(boundary)
            available=False
            for day in sorted(days):
                matching=[p for p in peers if p.starts_on<=day and (not p.ends_on or p.ends_on>=day)]
                if len(matching)!=1 or matching[0].pk!=price.pk:continue
                try:default_cost(data,ticket_id,day.isoformat())
                except (ValueError,KeyError,TypeError):continue
                available=True;break
            if not available:continue
            service.card_price=price.price
            if option:
                service.card_ticket_title=option.title;service.card_ticket_title_en=option.title_en or option.title
            else:
                service.card_ticket_title='Vé mặc định';service.card_ticket_title_en='Standard ticket'
            break
    return services
