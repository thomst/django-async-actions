from celery import Task
from celery import shared_task
from celery import states
from .utils import import_content_type
from .utils import dyn_import


class ActionTask(Task):
    """
    _summary_
    """

    #: We update the result state ourselves.
    ignore_result = True

    def __init__(self):
        super().__init__()
        self._context = None

    def _store_context(self, state=None):
        # FIXME: Not sure what it costs to get current state here. In most cases
        # it would be fine to just use STARTED as state.
        state = state or self.backend.get_state(self.request.id)
        self.update_state(state=state, meta=self._context)

    def before_start(self, task_id, args, kwargs):
        """
        Prepare the context attribute.
        """
        self._context = dict()
        self._context['task_id'] = task_id
        self._context['task_name'] = self.name
        self._context['obj'] = args[0]
        self._context['notes'] = list()
        self._store_context(states.STARTED)

    def on_success(self, retval, task_id, args, kwargs):
        self._store_context(states.SUCCESS)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self._context['exc_message'] = str(exc)
        self._context['exc_type'] = type(exc).__name__
        self._context['exc_module'] = type(exc).__module__
        self._context['traceback'] = str(einfo)
        self._store_context(states.FAILURE)

    def add_note(self, note, level='info'):
        notes = self._context.get('notes', list())
        notes.append(dict(content=note, level=level))
        self._context['notes'] = notes
        self._store_context()

    @staticmethod
    def _resolve_object(obj):
        # FIXME: Can we do some caching for the content-type?
        if isinstance(obj, (tuple, list)):
            ContentType = import_content_type()
            ct = ContentType.objects.get_for_id(obj[0])
            obj = ct.get_object_for_this_type(pk=obj[1])
        return obj

    def __call__(self, obj, *args, **kwargs):
        """
        _summery_
        """
        # Let's pass in a real object as first argument.
        obj = self._resolve_object(obj)
        return super().__call__(obj, *args, **kwargs)


# To be sure not to use the ActionTask class here - even if configured globally
# as the class to be used - we set the base parameter explicitly.
@shared_task(base=Task)
def callback_release_lock(task_id):
    ObjectTaskState = dyn_import('async_actions.models', 'ObjectTaskState')
    state = ObjectTaskState.objects.get(task_id=task_id)
    state.active = False
    state.save(update_fields=('active',))


@shared_task(base=Task)
def errorback_release_lock(request, exc, traceback):
    callback_release_lock(request.id)
