from django.contrib import admin
from .models import ActionTaskState


class ActionTaskModelAdmin(admin.ModelAdmin):
    class Media:
        js = ["admin/js/task-monitoring.js"]


@admin.register(ActionTaskState)
class ActionTaskResultAdmin(admin.ModelAdmin):
    pass