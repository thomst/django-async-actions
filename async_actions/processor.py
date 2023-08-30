
import sys
import importlib
from celery import group


# We need to import ContentType dynamically because on celery app initialization
# the django apps are not yet loaded.
def import_content_type_cls():
    if not hasattr(sys.modules[__name__], 'ContentType'):
        ct_module = importlib.import_module('django.contrib.contenttypes.models')
        setattr(sys.modules[__name__], 'ContentType', getattr(ct_module, 'ContentType'))
    return getattr(sys.modules[__name__], 'ContentType')


class AsyncContext(dict):
    """
    An AsyncContext is a dict type that handles specific dict items to be
    serializable. Every :class:`~.task.ActionTask` takes a AsyncContext object
    as its first and only argument.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make sure obj item is serializeable.
        self._obj = None
        if 'obj' in self.data and not isinstance(self.data['obj'], (tuple, list)):
            obj = self.get('obj')
            ContentType = import_content_type_cls()
            ct_id = ContentType.objects.get_for_model(type(obj)).id
            self.data['obj'] = (ct_id, obj.pk)

    @property
    def obj(self):
        """
        Resolve the content-type-id and object-id into a real object.
        """
        if 'obj' in self.data and not self._obj:
            ContentType = import_content_type_cls()
            ct = ContentType.objects.get_for_id(self.data['obj'][0])
            self._obj = ct.get_object_for_this_type(pk=self.data['obj'][1])
        return self._obj

    @property
    def data(self):
        """
        Just a representation of self to have a consistent api along with the
        extra properties.
        """
        return self


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

    #: Class used as context when initiating the tasks signature.
    ASYNC_CONTEXT_CLS = AsyncContext

    def __init__(self, queryset, task, runtime_data=None):
        self._queryset = queryset
        self.task = task
        self.runtime_data = runtime_data or dict()
        self._locked_objects = list()
        self._results = list()
        self._signatures = None
        self._workflow = None

    def _get_object_lock(self, obj, task_id):
        """
        Try to get a lock for the object.
        """
        return True

    def _get_context(self, obj):
        """
        _summary_
        """
        return self.ASYNC_CONTEXT_CLS(obj=obj, runtime_data=self.runtime_data)

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
        return self.task.si(self._get_context(obj))

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
    def objects(self):
        """
        Return a list of all objects of the passed in queryset.
        """
        return list(self._queryset)

    @property
    def locked_objects(self):
        """
        Objects that were locked. This property will be an empty list until the
        :meth:`.run` method was called.
        """
        return self._locked_objects

    @property
    def results(self):
        """
        Results returned from the workflow.delay call. Results will be available
        after the :meth:`.run` method was called. Before that this will be an
        empty list.
        """
        return self._results

    @property
    def signatures(self):
        """
        List of signatures for all objects that are not locked.
        """
        if self._signatures is None:
            self._signatures = list()
            for obj in self.objects:
                signature = self._get_signature(obj)
                signature.freeze()
                if self._get_object_lock(obj, signature.id):
                    self._signatures.append(signature)
                else:
                    self._locked_objects.append(obj)
        return self._signatures

    @property
    def workflow(self):
        """
        List of signatures for all objects that are not locked.
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
        return self._results
