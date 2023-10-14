from item_messages.constants import INFO
from celery import Task
from celery import shared_task
from celery.utils.time import get_exponential_backoff_interval
from .models import ActionTaskState
from .locks import get_locks as get_locks_
from .locks import release_locks as release_locks_
from .exceptions import OccupiedLockException


class ActionTask(Task):
    """
    _summary_
    """

    #: Results must not be ignored and tracked for started tasks.
    ignore_result = False
    track_started = True

    #: Let the worker know about our occupied lock exception.
    throws = (OccupiedLockException,)

    #: Retry policy for occupied lock exceptions.
    locked_max_retries = 12
    locked_retry_delay = 60
    locked_retry_backoff = 3
    locked_retry_backoff_max = 300
    locked_retry_jitter = True

    #: Be sure there are defaults for some extra task attributes we use.
    _state = None
    _locks = None

    def get_locks(self, *lock_ids):
        try:
            return get_locks_(*lock_ids)
        except OccupiedLockException as exc:
            if self.locked_retry_backoff:
                countdown = get_exponential_backoff_interval(
                    factor=int(max(1,0, self.locked_retry_backoff)),
                    retries=self.request.retries,
                    maximum=self.locked_retry_backoff_max,
                    full_jitter=self.locked_retry_jitter,
                )
            else:
                countdown = self.locked_retry_delay
            self.retry(
                exc=exc,
                countdown=countdown,
                max_retries=self.locked_max_retries,
            )

    def before_start(self, task_id, args, kwargs):
        """
        _summary_
        """
        # Since Tasks instances might be reused within one worker process we
        # explicitly set the state to None.
        self._state = None

        # Get locks if some lock ids were passed in as header.
        try:
            lock_ids = self.request.headers['lock_ids']
        except (TypeError, KeyError):
            self._locks = None
        else:
            self._locks = self.get_locks(*lock_ids)

    @property
    def state(self):
        """
        _summary_
        """
        if not self._state:
            # TODO: Select-related the state object.
            self._state = ActionTaskState.objects.get(task_id=self.request.id)
        return self._state

    def run_with(self, state):
        """
        To run an action task from within another we pass in the state of the
        parent task. Calling the task could be chained since we return the task
        itself::

            mytask.run_with(state_of_parent_task)(*args, **kwargs)

        :param :class:`~.models.ActionTaskState` state: action task state
        :return :class:`~.ActionTask`: the task itself
        """
        self._state = state
        return self

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._locks:
            release_locks_(*self._locks)

    @property
    def obj(self):
        """
        _summary_
        """
        return self.state.obj

    @property
    def notes(self):
        """
        _summary_
        """
        return self.state.notes

    def add_note(self, note, level=INFO):
        """
        _summary_
        """
        self.state.notes.create(note=note, level=level)


@shared_task(bind=True, base=ActionTask)
def get_locks(self, *lock_ids):
    self.get_locks(*lock_ids)


@shared_task(base=Task)
def release_locks(*lock_ids):
    release_locks_(*lock_ids)


@shared_task(base=Task)
def release_locks_on_error(request, exc, traceback, *lock_ids):
    # Do not release locks if the exception was an occupied lock exception. In
    # this case we have nothing to do here.
    if not isinstance(exc, OccupiedLockException):
        release_locks_(*lock_ids)
