import time
from celery.result import AsyncResult
from item_messages import add_message, ERROR
from .messages import add_task_message
from .processors import Processor


class BaseTaskAction:
    """
    Base class for admin actions running a session.
    """
    def __init__(self, task, processor_cls=None, description=None, permissions=None, runtime_data=None):
        self.task = task
        self.processor_cls = processor_cls or Processor
        self.runtime_data = runtime_data or dict()
        self.short_description = description or f'run {task.__name__}'
        if permissions:
            self.allowed_permissions = permissions

    @property
    def __name__(self):
        return self.task.__name__

    def run(self, modeladmin, request, queryset, runtime_data=None):
        """
        _summary_

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        """
        processor = self.processor_cls(queryset, self.task, runtime_data)
        processor.run()
        for sig in processor.signatures:
            obj = [o for o in processor.objects if o.pk == sig.args[0][1]][0]
            add_task_message(request, obj, sig)

        for obj in processor.locked_objects:
            msg = 'There is already a running action task for this object.'
            add_message(request, ERROR, obj, msg)

        time.sleep(3)
        for result in processor.results:
            result = AsyncResult(result.task_id)
            print(result.result)
            add_task_message(request, obj, result)

    def __call__(self, modeladmin, request, queryset):
        """
        Make the action object a callable

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        """
        self.run(modeladmin, request, queryset, self.runtime_data)


class TaskAction(BaseTaskAction):
    """
    _summary_
    """
    forms = list()
    """
    _summary_
    """
    def run(self, modeladmin, request, queryset, runtime_data=None):
        """
        _summary_

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        """
        # TODO: Do form processing here and pass the form.cleaned_data.
        runtime_data = dict()
        super().run(modeladmin, request, queryset, runtime_data)



def as_action(*args, **options):
    """
    _summery_
    """
    def create_action_from_task(**options):

        def _inner(func):
            action_cls = options.get('action_cls', TaskAction)
            processor_cls = options.get('processor_cls', Processor)
            return action_cls(func, processor_cls)
        return _inner

    # Usage as decorator without parameters or as function.
    if len(args) == 1 and callable(args[0]):
        return create_action_from_task(**options)(args[0])

    # Usage as decorator with parameters.
    else:
        return create_action_from_task(**options)
