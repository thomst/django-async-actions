from django.contrib import admin
from item_messages.actions import clear_item_messages
from async_actions.actions import as_action
from async_actions.admin import ActionTaskModelAdmin
from async_actions.models import ObjectTaskState
from .models import TestModel
from .tasks import test_task
from .tasks import task_with_arg
from .tasks import task_with_kwargs
from .tasks import task_that_fails


@admin.register(TestModel)
class TestModelAdmin(ActionTaskModelAdmin):
    list_display = ['id', 'one', 'two', 'three']
    actions = [
        as_action(test_task),
        as_action(task_with_arg.s('foobar')),
        as_action(task_with_kwargs.s(foo='bar'), runtime_data=dict(bar='foo')),
        as_action(task_that_fails),
        clear_item_messages,
        ]


@admin.register(ObjectTaskState)
class ObjectTaskStateAdmin(admin.ModelAdmin):
    pass