from decimal import Decimal,InvalidOperation
from django import template
register=template.Library()

@register.filter
def vnd(value):
    try:return f'{Decimal(value):,.0f}'.replace(',','.')+' đ'
    except (InvalidOperation,TypeError,ValueError):return '—'
