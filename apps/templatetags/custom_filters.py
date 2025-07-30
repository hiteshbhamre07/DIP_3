# custom_filters.py
from django import template

register = template.Library()

@register.filter
def replace(value):
    """Replace underscores with spaces and capitalize words."""
    if value:
        return value.replace('_', ' ').title()
    return value


@register.filter
def zip_lists(a, b):
    return zip(a, b)