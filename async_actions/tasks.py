from item_messages.constants import INFO
from celery import Task
from celery import shared_task
from .models import ActionTaskState
from .locks import get_object_lock
from .locks import release_locks


class ActionTask(Task):
    """
    _summary_
    """

    ignore_result = False
    track_started = True
    _state = None

    def setup(self, state=None):
        """
        _summary_

        :param :class:`~.models.ActionTaskState` state: action task state
        """
        if state:
            self._state = state
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


class ObjectLockActionTaskMixin:
    """
    _summary_

    :param _type_ ActionTask: _description_
    """

    #: List of lock-ids.
    _locks = None

    def setup(self, state=None):
        super().setup(state)
        if not state:
            self._locks = [get_object_lock(self._state.obj)]

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo)
        release_locks(*self._locks)


class ObjectLockActionTask(ObjectLockActionTaskMixin, ActionTask):
    """
    _summary_
    """


@shared_task(base=Task)
def release_locks_task(*lock_ids):
    release_locks(*lock_ids)
