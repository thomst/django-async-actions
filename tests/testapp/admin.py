from django.contrib import admin
from item_messages.actions import clear_item_messages
from async_actions.actions import as_action
from .models import TestModel
from .tasks import test_task


@admin.register(TestModel)
class TestModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'one', 'two', 'three']
    actions = [as_action(test_task), clear_item_messages]
