from django.contrib import admin
from .models import ActionTaskResult


class ActionTaskModelAdmin(admin.ModelAdmin):
    class Media:
        js = ["admin/js/task-monitoring.js"]


@admin.register(ActionTaskResult)
class ActionTaskResultAdmin(admin.ModelAdmin):
    pass