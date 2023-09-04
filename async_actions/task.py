from celery import Task
from .utils import import_content_type
from .utils import dyn_import


# FIXME: Do some caching with the content_type_id. (If not done by ContentType.)
class AsyncContext(dict):
    """
    An AsyncContext is a dict type that handles specific dict items to be
    serializable. Every :class:`~.task.ActionTask` takes a AsyncContext object
    as its first and only argument.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Resolve object into serializable tuple of content_type_id and
        # object_id.
        self._obj = None
        if 'obj' in self.data and not isinstance(self.data['obj'], (tuple, list)):
            obj = self.get('obj')
            ContentType = import_content_type()
            ct_id = ContentType.objects.get_for_model(type(obj)).id
            self.data['obj'] = (ct_id, obj.pk)

    @property
    def obj(self):
        """
        Resolve the content-type-id and object-id into a real object.
        """
        if (
                not self._obj
                and 'obj' in self.data
                and isinstance(self.data['obj'], (tuple, list))
            ):
            ContentType = import_content_type()
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
    def __init__(self):
        super().__init__()
        self._context = None

    def before_start(self, task_id, args, kwargs):
        """
        Get object to work with.
        """

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Release object lock.
        """
        ObjectTaskState = dyn_import('async_actions.models', 'ObjectTaskState')
        state = ObjectTaskState.objects.get(task_id=task_id)
        state.active = False
        state.save(update_fields=('active',))

    def add_note(self, note, level='info'):
        notes = self.context.get('notes', list())
        notes.append(dict(content=note, level=level))
        self.context['notes'] = notes
        self.store_context()

    def store_context(self):
        state = self.backend.get_state(self.request.id)
        self.update_state(state=state, meta=self.context)

    @property
    def context(self):
        """
        _summary_
        """
        return self._context

    @property
    def c(self):
        """
        _summary_
        """
        return self._context

    def _init_context(self, context):
        # Add task name to context to have it at hand in our AsyncResults.
        context['task_name'] = self.name
        if isinstance(context, self.ASYNC_CONTEXT_CLS):
            self._context = context
        else:
            self._context = self.ASYNC_CONTEXT_CLS(**context)

    # FIXME: Better not using self.context since we already have the context arg.
    def __call__(self, context, *args, **kwargs):
        """
        If called with a tuple of a content_type id and object id as first
        argument we do a lookup and pass the "real" object to the super method.
        This
        """
        self._init_context(context)
        self.context['task_result'] = super().__call__(self.context, *args, **kwargs)
        return self.context
