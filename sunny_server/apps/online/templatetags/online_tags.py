from django import template
register=template.Library()
@register.simple_tag(takes_context=True)
def ot(context,vi,en):return en if context.get('lang')=='en' else vi

@register.simple_tag(takes_context=True)
def money(context,value):
    try:result=format(int(value),',')
    except (TypeError,ValueError):return '—'
    return result if context.get('lang')=='en' else result.replace(',','.')

from ..richtext import render_body
register.filter("service_body",render_body)
