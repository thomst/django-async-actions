
from celery import group
from celery import states
from django.contrib.contenttypes.models import ContentType
from .models import ActionTaskState
from .models import Lock
from .tasks import release_locks


class Processor:
    """
    A processor builds a celery workflow for a specific
    :class:`~.task.ActionTask` and queryset and launches this workflow.
    Therefore it iterates the queryset and does the following for each object:

    * Check if there is not already an action-task running for the given object.
    * Create a :class:`~celery.canvas.Signature` from the task passing the
      object and runtime data as arguments.
    * Wrap those signatures together to a `celery workflow
      <https://docs.celeryq.dev/en/stable/userguide/canvas.html>`_.

    :param session_class: the session class to be processed
    :type session_class: :class:`~.sessions.BaseSession`
    :param user: django user that initiated the session processing
    :type user: :class:`~django.contrib.auth.models.User`
    :param queryset: the queryset to be processed
    :type queryset: :class:`~django.db.models.query.QuerySet`
    :param runtime_data: data to be passed to the
        :meth:`.sessions.BaseSession.run` method of each session
    :type runtime_data: any serialize able object, probably a dict
    """

    def __init__(self, queryset, sig, runtime_data=None):
        self._sig = sig
        self._queryset = queryset
        self._runtime_data = runtime_data or dict()
        self._results = list()
        self._task_states = list()
        self._locked_objects = list()
        self._signatures = None
        self._workflow = None

    def _get_locks(self, obj):
        """
        Get locks for an object and related resources. Return a tuple of
        lock-ids or None if a lock couldn't be preserved.

        :return tuple: tuple of lock-ids
        :raise OccupiedLockException: If a lock couldn't be achieved.
        """
        checksum = hash((obj.id, type(obj).__name__, type(obj).__module__))
        lock_id = Lock.objects.get_lock(checksum)
        return (lock_id,)

    def _get_task_state(self, obj, signature):
        """
        Create :class:`~.models.TaskState` instance for a signature or for all
        signatures of a :class:`~celery.canvas.chain`.

        :param obj: object to run the action task with
        :type obj: :class:`~django.db.models.Model`
        :param signature: signature or chain
        :type signature: :class:`~celery.canvas.Signature` or :class:`~celery.canvas.chain`
        :return list of :class:`~.models.TaskState`: list of TaskState instances
        """
        content_type = ContentType.objects.get_for_model(type(obj))
        params = dict(
            ctype=content_type,
            obj_id=obj.pk,
            task_id=signature.id,
            task_name=signature.task,
            status=states.PENDING
        )
        task_state = ActionTaskState(**params)
        task_state.save()
        return task_state

    def _get_signature(self, locks):
        """
        _summary_

        :return _type_: _description_
        """
        # Clone the original signature and use freeze with it to have a valid
        # task-id.
        sig = self._sig.clone()
        sig.freeze()

        # If a lock was setup we equip the signature with release callbacks.
        if locks:
            sig.set(link=release_locks.si(*locks))
            sig.set(link_error=release_locks.si(*locks))

        return sig

    def _get_signatures(self):
        """
        _summary_

        :return _type_: _description_
        """
        signatures = list()
        for obj in self._queryset:
            try:
                locks = self._get_locks(obj)
            except OccupiedLockException:
                self._locked_objects.append(obj)
            else:
                signature = self._get_signature(locks)
                signatures.append(signature)

                # For primitives we loop over the tasks attribute of the
                # signature. Otherwise we simply use the signature in a
                # one-item-list.
                task_states = list()
                for sig in getattr(signature, 'tasks', [signature]):
                    task_states.append(self._get_task_state(obj, sig))
                self._task_states.append(task_states)

        return signatures

    def _get_workflow(self):
        """
        Build a celery workflow. See also
        `https://docs.celeryq.dev/en/stable/userguide/canvas.html#the-primitives`_.
        By default we build a simple :class:`~celery.canvas.group` of all
        signatures we got. By overwriting this method it is possible to build
        more advanced workflows.

        :return :class:`~celery.canvas.Signature: celery workflow
        """
        return group(*self.signatures)

    @property
    def results(self):
        """
        Results returned from the workflow.delay call. Populated by :meth:`.run`
        method.
        """
        return self._results

    @property
    def task_states(self):
        """
        Nested list of :class:`.models.ActionTaskState` instances. If not
        working with a :class:`~celery.canvas.chain` the inner lists have only a
        single item. Populated by :meth:`.run` method.
        """
        return self._task_states

    @property
    def locked_objects(self):
        """
        :class:`.models.ActionTaskResult` instances that were locked. Populated
        by :meth:`.run` method.
        """
        return self._locked_objects

    @property
    def signatures(self):
        """
        List of signatures for all objects that are not locked. Populated by
        :meth:`.run` method.
        """
        if self._signatures is None:
            self._signatures = self._get_signatures()
        return self._signatures

    @property
    def workflow(self):
        """
        List of signatures for all objects that are not locked. Set by
        :meth:`.run` method.
        """
        if self._workflow is None:
            self._workflow = self._get_workflow()
        return self._workflow

    def run(self):
        """
        Run the workflow build by :meth:`.get_workflow`. By default we do a
        simple :meth:`~celery.canvas.Signature.delay` call.

        :return :class:`~celery.result.AsyncResult: result object
        """
        self._results = self.workflow.delay(**self._runtime_data)
        self._results.save()
        return self._results
