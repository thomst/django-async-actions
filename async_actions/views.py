import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import permission_required
from .messages import update_task_message
from .models import ActionTaskState


@require_GET
@permission_required("async_actions.view_actiontaskresult", raise_exception=True)
def update_task_messages(request):
    """
    _summary_
    """
    data = json.loads(request.GET['msgs'])
    updated_messages = {}
    states = ActionTaskState.objects.filter(task_id__in=data.keys())

    for state in states:
        msg_id = data[state.task_id]['msg_id']
        task_status = data[state.task_id]['task_status']
        note_count = data[state.task_id]['note_count']

        # See if something has changed since rendered the message.
        if state.status == task_status and state.notes.count() == note_count:
            continue

        # Set the task message and build the json response list.
        msg = update_task_message(request, msg_id, state)
        updated_messages[msg.id] = msg.html

    return JsonResponse(updated_messages)
