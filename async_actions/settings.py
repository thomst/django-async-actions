# -*- coding: utf-8 -*-

from django.conf import settings
from .processor import Processor


ASYNC_ACTIONS_PROCESSOR_CLS = getattr(settings, 'ASYNC_ACTIONS_PROCESSOR_CLS', Processor)
