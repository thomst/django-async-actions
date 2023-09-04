from celery.result import AsyncResult
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from item_messages import add_message, clear_messages
from item_messages import INFO
from .utils import get_result_hash


class ProxyResult:
    """
    Build a :class:`~celery.result.AsyncResult` like object from a
    :class:`~celery.canvas.Signature`.

    Results of pending tasks are not populated by any data at all. To render a
    message for a pending task we use fed a :class:`.ProxyResult` with data from
    a signature and use it within our message instead of a real result object.
    """
    def __init__(self, signature):
        self.task_id = signature.id
        self.state = 'PENDING'
        self.result = self.info = dict(task_name=signature.task)


def build_task_message(result):
    if not isinstance(result, AsyncResult):
        result = ProxyResult(result)
    template = 'async_actions/action_task.html'
    msg = render_to_string(template, dict(result=result, result_hash=get_result_hash(result)))
    return mark_safe(msg)


def add_task_message(request, obj, result):
    msg = build_task_message(result)
    add_message(request, INFO, obj, msg)
    return msg


def set_task_message(request, obj, result):
    clear_messages(request, obj)
    return add_task_message(request, obj, result)
