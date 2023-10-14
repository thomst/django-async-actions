
from celery import group
from celery import states
from django.contrib.contenttypes.models import ContentType
from .models import ActionTaskState
from .locks import get_object_checksum
from .tasks import get_locks
from .tasks import release_locks
from .tasks import release_locks_on_error


class LOCK_MODE:
    #: Task based locking.
    INNER = 'inner'

    #: Chain based locking.
    OUTER = 'outer'

    #: Disabled locking.
    NONE = None


class Processor:
    """
        A processor builds a celery workflow for a specific
    :class:`~.task.ActionTask` and queryset and launches this workflow.

    :param _type_ queryset: _description_
    :param _type_ sig: _description_
    :param _type_ runtime_data: _description_, defaults to None
    :param bool inner_lock: _description_, defaults to True
    :param bool outer_lock: _description_, defaults to False
    """
    # TODO: Overwork inner and outer lock api.
    def __init__(self, queryset, sig, runtime_data=None, lock_mode=LOCK_MODE.INNER):
        self._sig = sig
        self._queryset = queryset
        self._runtime_data = runtime_data or dict()
        self._lock_mode = lock_mode
        self._results = list()
        self._task_states = list()
        self._signatures = None
        self._workflow = None

    def _get_lock_ids(self, obj):
        """
        _summary_

        :param _type_ obj: _description_
        """
        lock_id = get_object_checksum(obj)
        return [lock_id]

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
        return task_state

    def _get_signature(self, obj):
        """
        _summary_

        :return _type_: _description_
        """
        # Clone original signature and add runtime data as kwargs.
        # FIXME: sig.clone(kwargs=self._runtime_data) does not work for chained
        # tasks. See: https://github.com/celery/celery/issues/5193.
        sig = self._sig.clone(kwargs=self._runtime_data)

        # Pass the lock ids as headers and let the task handle the locks.
        if self._lock_mode == LOCK_MODE.INNER:
            lock_ids = self._get_lock_ids(obj)
            sig = sig.clone(headers={'lock_ids': lock_ids})

        # Chain a get_locks task with the original signature and equip the chain
        # with a release_locks task as callback.
        elif self._lock_mode == LOCK_MODE.OUTER:
            lock_ids = self._get_lock_ids(obj)
            # Make the signature immutable. Otherwise it would recieve a `None`
            # as positional argument from the get_locks task.
            sig.set_immutable(True)
            sig = get_locks.si(*lock_ids) | sig
            sig.set(link=release_locks.si(*lock_ids))
            sig.set(link_error=release_locks_on_error.s(*lock_ids))

        return sig

    def _get_signatures(self):
        """
        _summary_

        :return _type_: _description_
        """
        signatures = list()
        for obj in self._queryset:
            signature = self._get_signature(obj)
            signature.freeze()
            signatures.append(signature)

            # For primitives we loop over the tasks attribute of the
            # signature. Otherwise we simply use the signature in a
            # one-item-list.
            task_states = list()
            for sig in getattr(signature, 'tasks', [signature]):
                task_state = self._get_task_state(obj, sig)
                task_state.save()
                task_states.append(task_state)
            self._task_states.append(task_states)

        return signatures

    def _get_workflow(self):
        """
        Build a celery workflow. See also
        `https://docs.celeryq.dev/en/stable/userguide/canvas.html#the-primitives`_.
        By default we build a simple :class:`~celery.canvas.group` of all
        signatures we got. By overwriting this method it is possible to build
        more advanced workflows.

        :return :class:`~celery.canvas.group`: celery workflow
        """
        return group(*self.signatures)

    # FIXME: Do we need results property?
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

    # FIXME: Do we need signatures and workflow properties?
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
        # FIXME: Do we want to use runtime-data as positional argument for
        # better chain support:
        # args = [self._runtime_data] if self._runtime_data else []
        # self._results = self.workflow.delay(*args)
        self._results = self.workflow.delay()
        self._results.save()
        return self._results
