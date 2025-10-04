from django import template
from urllib.parse import urlencode

register = template.Library()

@register.filter
def querystring_without_page(get_dict):
    """Remove page parameter from querystring for pagination links"""
    mutable_dict = get_dict.copy()
    if 'page' in mutable_dict:
        del mutable_dict['page']
    
    query = urlencode(mutable_dict)
    return f'&{query}' if query else ''
