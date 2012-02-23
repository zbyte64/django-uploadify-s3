from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('uploadify_head.html')
def uploadify_head():
    return {
        'STATIC_URL': settings.STATIC_URL, 
    }

