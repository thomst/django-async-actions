from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import permission_required
from .messages import set_task_message
from .models import ActionTaskState
from .utils import get_message_checksum


@require_GET
@permission_required("async_actions.view_actiontaskresult", raise_exception=True)
def tasks_by_ids(request):
    """
    _summary_
    """
    task_data = request.GET
    response_tasks = dict()
    states = ActionTaskState.objects.filter(task_id__in=task_data.keys())
    for state in states:
        # If the checksum hasn't changed we skip the state.
        if get_message_checksum(state) == int(task_data[state.task_id]):
            continue

        # Set the task message and build the json response list.
        msg = set_task_message(request, state)
        response_tasks[state.task_id] = msg

    return JsonResponse(response_tasks)
