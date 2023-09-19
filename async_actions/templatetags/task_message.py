from django import template
from ..utils import get_message_checksum


register = template.Library()


@register.filter
def get_checksum(task):
    return get_message_checksum(task)