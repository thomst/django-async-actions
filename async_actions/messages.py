from celery import states
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from item_messages import add_message, clear_messages
from item_messages import INFO, ERROR


def build_task_message(task_state):
    template = 'async_actions/task_message.html'
    context = dict(task_state=task_state)
    msg = render_to_string(template, context)
    return mark_safe(msg)


def add_task_message(request, task_state):
    msg = build_task_message(task_state)
    if task_state.status == states.FAILURE:
        add_message(request, ERROR, task_state.obj, msg)
    else:
        add_message(request, INFO, task_state.obj, msg)
    return msg


def set_task_message(request, task_state):
    clear_messages(request, task_state.obj)
    return add_task_message(request, task_state)
