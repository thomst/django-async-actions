import sys
import importlib

# We need to import ContentType dynamically because on celery app initialization
# the django apps are not yet loaded.
def import_content_type():
    return dyn_import('django.contrib.contenttypes.models', 'ContentType')


def dyn_import(module, attr):
    if not hasattr(sys.modules[__name__], attr):
        ct_module = importlib.import_module(module)
        setattr(sys.modules[__name__], attr, getattr(ct_module, attr))
    return getattr(sys.modules[__name__], attr)


def get_message_checksum(task):
    """
    A checksum indicating an updated message.
    """
    return hash((task.status, task.notes.values_list('id', flat=True)))
