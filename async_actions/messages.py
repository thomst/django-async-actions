from celery.result import AsyncResult
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from item_messages import add_message
from item_messages import INFO


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
        self.task_name = signature.task
        self.task_args = signature.args
        self.task_kwargs = signature.kwargs
        self.state = 'PENDING'
        self.date_done = None
        self.traceback = None
        self.result = None


def get_task_message(result):
    if not isinstance(result, AsyncResult):
        result = ProxyResult(result)
    template = 'async_actions/message.html'
    msg = render_to_string(template, dict(result=result))
    return mark_safe(msg)


def add_task_message(request, obj, result):
    msg = get_task_message(result)
    add_message(request, INFO, obj, msg)
