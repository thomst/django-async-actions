from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import permission_required
from .messages import set_task_message
from .models import ActionTaskState


@require_GET
@permission_required("async_actions.view_actiontaskresult", raise_exception=True)
def tasks_by_ids(request):
    """
    _summary_
    """
    task_data = request.GET
    response_tasks = dict()
    task_results = ActionTaskState.objects.filter(task_id__in=task_data.keys())
    for result in task_results:
        # If the checksum hasn't changed we skip the result.
        if result.state_hash == int(task_data[result.task_id]):
            continue

        # Set the task message and build the json response list.
        msg = set_task_message(request, result)
        response_tasks[result.task_id] = msg

    return JsonResponse(response_tasks)
