from celery.result import AsyncResult
from celery import states
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from item_messages import add_message, clear_messages
from item_messages import INFO, ERROR
from .utils import get_result_hash


class ProxyResult:
    """
    Build a :class:`~celery.result.AsyncResult` like object from a
    :class:`~celery.canvas.Signature`.

    Results of pending tasks are not populated by any data at all. To render a
    message for a pending task we fed a :class:`.ProxyResult` with data from a
    signature and use it within our message instead of a real result object.
    """
    def __init__(self, signature):
        self.task_id = signature.id
        self.state = states.PENDING
        self.result = self.info = dict(task_name=signature.task)


def build_task_message(res_or_sig):
    if not isinstance(res_or_sig, AsyncResult):
        result = ProxyResult(res_or_sig)
    else:
        result = res_or_sig
    template = 'async_actions/action_task.html'
    context = dict(result=result, result_hash=get_result_hash(result))
    msg = render_to_string(template, context)
    return mark_safe(msg)


def add_task_message(request, obj, res_or_sig):
    msg = build_task_message(res_or_sig)
    if getattr(res_or_sig, 'successful', lambda: True)():
        add_message(request, INFO, obj, msg)
    else:
        add_message(request, ERROR, obj, msg)
    return msg


def set_task_message(request, obj, result):
    clear_messages(request, obj)
    return add_task_message(request, obj, result)
