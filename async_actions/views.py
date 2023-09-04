from celery import states
from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import permission_required
from .messages import set_task_message
from .models import ObjectTaskState
from .utils import get_result_hash


@require_GET
@permission_required("async_actions.view_objecttaskstate", raise_exception=True)
def tasks_by_ids(request):
    """
    _summary_

    :param _type_ request: _description_
    :param _type_ task_ids: _description_
    """
    tasks = request.GET
    response_tasks = dict()
    task_states = ObjectTaskState.objects.filter(task_id__in=tasks.keys())
    for task_state in task_states:

        # Get result by task-id.
        # FIXME: Is there a way to bulk-load results for better perfomance?
        result = AsyncResult(task_state.task_id)

        # PENDING results won't be updated.
        if result.status == states.PENDING:
            continue

        # If the checksum hasn't changed we skip the result.
        if str(get_result_hash(result)) == str(tasks[result.task_id]):
            continue

        # Set the task message.
        msg = set_task_message(request, task_state.obj, result)

        # Collect messages for JsonResponse.
        response_tasks[result.task_id] = msg

    return JsonResponse(response_tasks)
