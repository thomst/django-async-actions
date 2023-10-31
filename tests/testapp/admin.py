from django.contrib import admin
from item_messages.actions import clear_item_messages
from async_actions.actions import as_action
from async_actions.admin import ActionTaskModelAdmin
from async_actions.processor import Processor
from .models import TestModel
from .tasks import test_task
from .tasks import task_with_arg
from .tasks import task_with_kwargs
from .tasks import task_that_fails
from .tasks import long_running_task
from .tasks import debug_task
from .tasks import test_chain
from .tasks import test_group
from .tasks import test_group_that_fails
from .tasks import info_task
from .tasks import task_that_calls_other_tasks


@admin.register(TestModel)
class TestModelAdmin(ActionTaskModelAdmin):
    list_display = ['id', 'one', 'two', 'three']
    actions = [
        as_action(test_task),
        as_action(info_task),
        as_action(debug_task),
        as_action(long_running_task),
        as_action(task_that_calls_other_tasks),
        as_action(task_with_arg.s('foobar')),
        as_action(task_with_kwargs.s(foo='bar'), runtime_data=dict(bar='foo')),
        as_action(task_that_fails, lock_mode=Processor.CHAIN_LOCK),
        as_action(test_chain),
        as_action(test_group),
        as_action(test_group_that_fails),
        clear_item_messages,
        ]
