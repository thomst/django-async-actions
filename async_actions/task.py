import importlib
from celery import Task


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

    def __call__(self, obj, *args, **kwargs):
        """
        If called with a tuple of a content_type id and object id as first
        argument we do a lookup and pass the "real" object to the super method.
        This
        """
        if isinstance(obj, (tuple, list)):
            ct_models = importlib.import_module('django.contrib.contenttypes.models')
            ContentType = getattr(ct_models, 'ContentType')
            ct = ContentType.objects.get_for_id(obj[0])
            obj = ct.get_object_for_this_type(pk=obj[1])
        return super().__call__(obj, *args, **kwargs)
        # return self.AsyncResult(self.request.id).result
