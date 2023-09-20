
from celery import group
from celery import states
from django.contrib.contenttypes.models import ContentType
from .models import ActionTaskState
from .models import Lock
from .task import release_lock


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

    def _get_lock(self, obj):
        """
        Get a lock to run an action task for a specific object.
        """
        checksum = hash((obj.id, type(obj).__name__, type(obj.__module__)))
        lock, created = Lock.objects.get_or_create(checksum=checksum)
        return lock if created else None

    def _get_task_state(self, obj, signature):
        """
        Try to get a lock for the object.
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

    def _get_signature(self, lock=None):
        """
        Create an immutable :class:`~celery.canvas.Signature. See also
        `https://docs.celeryq.dev/en/stable/userguide/canvas.html#immutability`_.
        The object will be resolved into its content-type-id and object-id
        before passed as argument to the signature.

        :param obj: the object to run the session with
        :type obj: :class:`~django.db.models.Model`
        :return: celery signature
        :rtype: :class:`~celery.canvas.Signature
        """
        # Let's setup our signature by adding arguments and callbacks.
        # We now use freeze to have a valid id and use it with the
        # release-lock-callback that we subsequently add to the signature.
        sig = self._sig.clone(kwargs=self._runtime_data)
        sig.freeze()
        if lock:
            sig.set(link=release_lock.si(lock.checksum))
            sig.set(link_error=release_lock.si(lock.checksum))
        return sig

    def _get_signatures(self):
        signatures = list()
        for obj in self._queryset:
            lock = self._get_lock(obj)
            if lock:
                signature = self._get_signature(lock)
                self._task_states.append(self._get_task_state(obj, signature))
                signatures.append(signature)
            else:
                self._locked_objects.append(obj)
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
        :class:`.models.ActionTaskResult` instances we've created. Populated by
        :meth:`.run` method.
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
        self._results = self.workflow.delay()
        self._results.save()
        return self._results
