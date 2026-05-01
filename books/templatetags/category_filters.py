from django import template

register = template.Library()

@register.filter
def indent(category):
    """Create indentation based on category level"""
    return '&nbsp;&nbsp;&nbsp;' * category.level + '└─ ' if category.level > 0 else ''