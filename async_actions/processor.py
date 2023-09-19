
from celery import group
from celery import states
from django.contrib.contenttypes.models import ContentType
from .models import ActionTaskState
from .task import callback_release_lock
from .task import errorback_release_lock


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
    def __init__(self, queryset, task=None, sig=None, runtime_data=None):
        self._sig = sig or task.signature()
        self._queryset = queryset
        self._runtime_data = runtime_data or dict()
        self._results = list()
        self._task_results = list()
        self._locked_task_results = list()
        self._signatures = None
        self._workflow = None

    def _get_object_lock(self, obj, signature):
        """
        Try to get a lock for the object.
        """
        content_type = ContentType.objects.get_for_model(type(obj))
        params = dict(
            ctype=content_type,
            obj_id=obj.pk,
            active=True,
            defaults=dict(
                task_id=signature.id,
                task_name=signature.task,
                status=states.PENDING
            )
        )
        task_result, created = ActionTaskState.objects.get_or_create(params)
        if created:
            self._task_results.append(task_result)
        else:
            self._locked_task_results.append(task_result)
        return created

    def _get_signature(self, obj):
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
        sig.set(link=callback_release_lock.si(sig.id))
        sig.set(link_error=errorback_release_lock.s())
        return sig

    def _get_signatures(self):
        signatures = list()
        for obj in self._queryset:
            signature = self._get_signature(obj)
            if self._get_object_lock(obj, signature):
                signatures.append(signature)
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
    def task_results(self):
        """
        :class:`.models.ActionTaskResult` instances we've created. Populated by
        :meth:`.run` method.
        """
        return self._task_results

    @property
    def locked_task_results(self):
        """
        :class:`.models.ActionTaskResult` instances that were locked. Populated
        by :meth:`.run` method.
        """
        return self._locked_task_results

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
