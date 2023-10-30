from celery.canvas import Signature
from celery.app.task import Task
from .messages import add_task_message
from .settings import ASYNC_ACTIONS_PROCESSOR_CLS
from .utils import get_task_name
from .utils import get_task_verbose_name
from .utils import get_task_description


class BaseTaskAction:
    """
    Base class for admin actions running a session.
    """
    PROCESSOR_CLS = None

    # TODO: Is there are elegant way to distinct action class params from
    # processor class params?
    def __init__(self, sig=None, processor_cls=None, permissions=None,
                 runtime_data=None, lock_mode=None):
        self._sig = sig
        self._processor_cls = processor_cls or self.PROCESSOR_CLS or ASYNC_ACTIONS_PROCESSOR_CLS
        self._runtime_data = runtime_data or dict()
        self._lock_mode = lock_mode
        self._name = get_task_name(sig)
        self.short_description = get_task_verbose_name(sig)
        self.description = get_task_description(sig)
        if permissions:
            self.allowed_permissions = permissions

    @property
    def __name__(self):
        return self._name

    def _get_runtime_data(self):
        """
        _summary_
        """
        return self._runtime_data

    def run(self, modeladmin, request, queryset):
        """
        _summary_

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        """
        runtime_data = self._get_runtime_data()
        processor = self._processor_cls(queryset, self._sig, runtime_data, self._lock_mode)
        processor.run()

        for task_state in processor.task_states:
            add_task_message(request, task_state)

    def __call__(self, modeladmin, request, queryset):
        """
        Make the action object a callable

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        """
        self.run(modeladmin, request, queryset)


class FormTaskActionMixin:
    """
    _summary_
    """

    #: List of forms.
    forms = list()

    def _get_forms(self):
        """
        _summary_

        :return _type_: _description_
        """
        return self.forms

    def _get_runtime_data(self):
        """
        _summary_
        """
        # TODO: Get runtime-data from forms.
        return super()._get_runtime_data()


class TaskAction(FormTaskActionMixin, BaseTaskAction):
    """
    _summary_
    """


# FIXME: Do we use verbose_name or short_description as api?
def as_action(*args, **options):
    """
    _summery_

    :param :class:`~.TaskAction` action_cls: _description_
    :param :class:`~.processor.Processor` processor_cls: _description_
    :param str verbose_name: _description_
    :param str description: _description_
    :param list permissions: _description_
    :param dict runtime_data: _description_
    :param const lock_mode: _description_
    """
    def create_action_from_task(**options):

        def _inner(signature):
            if isinstance(signature, Task):
                signature = signature.signature()
            if 'verbose_name' in options:
                signature.verbose_name = options.pop('verbose_name')
            if 'description' in options:
                signature.description = options.pop('description')
            action_cls = options.pop('action_cls', TaskAction)
            return action_cls(sig=signature, **options)
        return _inner

    # Usage as decorator without parameters or as function.
    if len(args) == 1 and callable(args[0]):
        return create_action_from_task(**options)(args[0])

    # Usage as decorator with parameters.
    else:
        return create_action_from_task(**options)
