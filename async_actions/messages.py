from celery import states
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from item_messages import add_message
from item_messages import update_message
from item_messages import get_messages
from item_messages import INFO, ERROR
from .utils import get_task_message_checksum


def build_task_message(task_state):
    # Build message.
    template = 'async_actions/task_message.html'
    context = dict(task_state=task_state)
    msg = render_to_string(template, context)

    # Set level.
    if task_state.status in states.PROPAGATE_STATES:
        level = ERROR
    else:
        level = INFO

    # Set processing status and extra data.
    extra_data = {
        'task_id': task_state.task_id,
        'checksum': get_task_message_checksum(task_state),
    }
    return level, mark_safe(msg), task_state.status_tag, extra_data


def add_task_message(request, task_state):
    return add_message(request, task_state.obj, *build_task_message(task_state))


def update_task_message(request, msg_id, task_state):
    update_message(request, msg_id, *build_task_message(task_state))
    return get_messages(request, msg_id=msg_id)