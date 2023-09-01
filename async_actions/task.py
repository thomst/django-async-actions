from celery import Task
from .utils import import_content_type_cls


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


class ActionTask(Task):
    """
    _summary_
    """

    ASYNC_CONTEXT_CLS = AsyncContext
    """
    Class used as context when initiating the tasks signature.
    """

    def before_start(self, task_id, args, kwargs):
        """
        Get object to work with.
        """

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Release object lock.
        """

    def add_note(self, note):
        result = self.AsyncResult(self.request.id)
        notes = result.result.get('notes', list())
        notes.append(note)
        self.update_state(state=result.state, meta=dict(notes=notes))

    def resolve_context(self, context):
        if isinstance(context, self.ASYNC_CONTEXT_CLS):
            return context
        else:
            return self.ASYNC_CONTEXT_CLS(**context)

    def __call__(self, context, *args, **kwargs):
        """
        If called with a tuple of a content_type id and object id as first
        argument we do a lookup and pass the "real" object to the super method.
        This
        """
        context = self.resolve_context(context)
        context['result'] = super().__call__(context, *args, **kwargs)
        return context
