from celery import states
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from item_messages import add_message, clear_messages
from item_messages import INFO, ERROR


def build_task_message(result):
    template = 'async_actions/action_task.html'
    context = dict(result=result, meta=result.get_meta_data())
    msg = render_to_string(template, context)
    return mark_safe(msg)


def add_task_message(request, result):
    msg = build_task_message(result)
    if result.status == states.FAILURE:
        add_message(request, ERROR, result.obj, msg)
    else:
        add_message(request, INFO, result.obj, msg)
    return msg


def set_task_message(request, result):
    clear_messages(request, result.obj)
    return add_task_message(request, result)
