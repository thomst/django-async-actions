from django import template
from ..settings import ASYNC_ACTION_DEBUG_MESSAGES as DEBUG

register = template.Library()


@register.filter(name="format_traceback")
def format_traceback(value):
    if DEBUG:
        return value
    else:
        return value.splitlines()[-1]
