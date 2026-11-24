from django import template
register=template.Library()
@register.simple_tag(takes_context=True)
def ot(context,vi,en):return en if context.get('lang')=='en' else vi
