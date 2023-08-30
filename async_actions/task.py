from celery import Task
from .processor import AsyncContext


class ActionTask(Task):
    """
    _summary_
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

    @staticmethod
    def resolve_context(context):
        if isinstance(context, AsyncContext):
            return context
        else:
            return AsyncContext(**context)

    def __call__(self, context, *args, **kwargs):
        """
        If called with a tuple of a content_type id and object id as first
        argument we do a lookup and pass the "real" object to the super method.
        This
        """
        context = self.resolve_context(context)
        context['result'] = super().__call__(context, *args, **kwargs)
        return context
