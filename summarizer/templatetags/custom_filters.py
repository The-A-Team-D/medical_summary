from django import template
from django.utils.safestring import mark_safe
import markdown as md

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='markdown')
def markdown(value):
    """Convert markdown to HTML"""
    if value:
        return mark_safe(md.markdown(value))
    return ''

@register.filter(name='format_percentage')
def format_percentage(value):
    """Format a float as a percentage"""
    try:
        return f"{float(value) * 100:.2f}%"
    except (ValueError, TypeError):
        return '0.00%'

@register.filter(name='split')
def split(value, key):
    """Split a string by the key and return a list"""
    return value.split(key)

@register.filter(name='replace')
def replace(value, arg):
    """Replace all instances of the first argument with the second argument"""
    if value is None:
        return ''
    
    find, replace = arg.split('"')
    # Remove the leading colon
    find = find[1:]
    return value.replace(find, replace)