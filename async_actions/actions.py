from celery.app.task import Task
from django.shortcuts import render
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

    # TODO: Is there an elegant way to distinct action class params from
    # processor class params?
    def __init__(self, sig=None, processor_cls=None, permissions=None, lock_mode=None):
        self._sig = sig
        self._processor_cls = processor_cls or self.PROCESSOR_CLS or ASYNC_ACTIONS_PROCESSOR_CLS
        self._lock_mode = lock_mode
        self._name = get_task_name(sig)
        self.short_description = get_task_verbose_name(sig)
        self.description = get_task_description(sig)
        if permissions:
            self.allowed_permissions = permissions

    @property
    def __name__(self):
        return self._name

    def run(self, modeladmin, request, queryset, runtime_data=None):
        """
        _summary_

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        """
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
        return self.run(modeladmin, request, queryset)


class FormTaskActionMixin:
    """
    _summary_
    """
    #: List of form classes.
    forms = list()

    def __init__(self, *args, forms=None, **kwargs):
        self._forms = forms or []
        super().__init__(*args, **kwargs)

    def _get_forms(self):
        """
        _summary_

        :return _type_: _description_
        """
        return self.forms + self._forms

    def run(self, modeladmin, request, queryset, runtime_data=None):
        """
        _summary_

        :param _type_ modeladmin: _description_
        :param _type_ request: _description_
        :param _type_ queryset: _description_
        :return _type_: _description_
        """
        forms = []
        for form_cls in self._get_forms():
            if f'run_{self.__name__}' in request.POST:
                form = form_cls(request.POST)
            else:
                form = form_cls()
            forms.append(form)

        if not forms:
            return super().run(modeladmin, request, queryset)

        elif all(form.is_valid() for form in forms):
            runtime_data = {}
            for form in forms:
                runtime_data.update(form.cleaned_data)
            return super().run(modeladmin, request, queryset, runtime_data)

        else:
            context = dict(
                title=self.short_description,
                objects=queryset.order_by('pk'),
                forms=forms,
                action=self.__name__,
            )
            return render(request, 'async_actions/async_action_form.html', context)


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
    :param list forms: _description_
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
