"""English booking notifications; recipient selection stays in the payment workflow."""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation,timezone


def booking_context(order):
    cash=order.status=='pending' and order.payment_method=='cash'
    return {
        'order':order,
        'cash_request':cash,
        'title':'Ticket delivery request' if cash else 'Payment received',
        'status':'Awaiting contact & cash collection' if cash else 'Paid · Tickets awaiting fulfilment',
        'intro':('A customer has requested ticket delivery and cash collection in Da Nang. Please contact the customer to confirm the delivery arrangements.' if cash else 'Payment has been received for this booking. Please review the details below and arrange the customer’s tickets.'),
        'lines':[{'title':line.snapshot.get('title_en') or line.snapshot.get('title',''),'option':line.snapshot.get('option_en') or line.snapshot.get('option',''),'visit_date':line.visit_date,'qty':line.qty,'unit_price':format(line.unit_price,','),'total':format(line.total,',')} for line in order.lines.all()],
        'total':format(order.total,','),
        'method':'Cash on ticket delivery · Da Nang' if cash or order.payment_method=='cash' else 'Bank transfer via QR',
        'process_url':settings.PUBLIC_SITE_URL.rstrip('/')+'/online/staff/cart/'+str(order.pk)+'/',
        'logo_url':settings.PUBLIC_SITE_URL.rstrip('/')+'/static/img/sunny-logo.png',
    }

def booking_notification(order,address):
    context=booking_context(order)
    subject='Sunny | '+('Delivery request' if context['cash_request'] else 'Payment received')+' | '+order.code
    with translation.override('en'),timezone.override('Asia/Ho_Chi_Minh'):
        plain=render_to_string('online/email/booking_notification.txt',context)
        html=render_to_string('online/email/booking_notification.html',context)
    message=EmailMultiAlternatives(subject,plain,to=[address])
    message.attach_alternative(html,'text/html')
    return message
