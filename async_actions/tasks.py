from item_messages.constants import INFO
from celery import Task
from celery import shared_task
from .models import ActionTaskState
from .models import Lock


class ActionTask(Task):
    """
    _summary_
    """

    ignore_result = False
    track_started = True
    _state = None

    def setup(self, parent=None):
        """
        _summary_

        :param :class:`~.ActionTask` parent: calling action task
        """
        if parent:
            self._state = parent._state
        else:
            self._state = ActionTaskState.objects.get(task_id=self.request.id)

    def before_start(self, task_id, args, kwargs):
        """
        _summary_
        """
        self.setup()

    @property
    def obj(self):
        """
        _summary_
        """
        return self._state.obj

    @property
    def notes(self):
        """
        _summary_
        """
        return self._state.notes

    def add_note(self, note, level=INFO):
        """
        _summary_
        """
        self.notes.create(note=note, level=level)


# To be sure not to use the ActionTask class here - even if configured globally
# as the class to be used - we set the base parameter explicitly.
@shared_task(base=Task)
def release_locks(*lock_ids):
    for lock_id in lock_ids:
        Lock.objects.get(checksum=int(lock_id)).delete()
