import sys
import importlib

# We need to import ContentType dynamically because on celery app initialization
# the django apps are not yet loaded.
def import_content_type_cls():
    if not hasattr(sys.modules[__name__], 'ContentType'):
        ct_module = importlib.import_module('django.contrib.contenttypes.models')
        setattr(sys.modules[__name__], 'ContentType', getattr(ct_module, 'ContentType'))
    return getattr(sys.modules[__name__], 'ContentType')


