from django.contrib import admin
from item_messages.actions import clear_item_messages
from async_actions.actions import as_action
from async_actions.admin import ActionTaskModelAdmin
from async_actions.models import ObjectTaskState
from .models import TestModel
from .tasks import test_task


@admin.register(TestModel)
class TestModelAdmin(ActionTaskModelAdmin):
    list_display = ['id', 'one', 'two', 'three']
    actions = [as_action(test_task), clear_item_messages]


@admin.register(ObjectTaskState)
class ObjectTaskStateAdmin(admin.ModelAdmin):
    pass