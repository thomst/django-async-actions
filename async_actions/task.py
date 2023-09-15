from item_messages.constants import INFO
from celery import Task
from celery import shared_task
from .models import ActionTaskResult


class ActionTask(Task):
    """
    _summary_
    """

    #: We update the result state ourselves.
    ignore_result = False
    track_started = True


    def __init__(self):
        super().__init__()
        self._action = None

    def before_start(self, task_id, args, kwargs):
        """
        _summary_
        """
        self._action = ActionTaskResult.objects.get(task_id=self.request.id)

    @property
    def obj(self):
        """
        _summary_
        """
        return self._action.obj

    @property
    def notes(self):
        """
        _summary_
        """
        return self._action.notes

    def add_note(self, note, level=INFO):
        """
        _summary_
        """
        self.notes.create(note=note, level=level)


# To be sure not to use the ActionTask class here - even if configured globally
# as the class to be used - we set the base parameter explicitly.
@shared_task(base=Task)
def callback_release_lock(task_id):
    task_result = ActionTaskResult.objects.get(task_id=task_id)
    task_result.active = False
    task_result.save(update_fields=('active',))


@shared_task(base=Task)
def errorback_release_lock(request, exc, traceback):
    callback_release_lock(request.id)
