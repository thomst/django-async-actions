from django.contrib import admin
from django_celery_results.admin import TaskResultAdmin
from .models import ActionTaskResult


class ActionTaskResultAdmin(TaskResultAdmin):
    """
    _summary_
    """


admin.site.register(ActionTaskResult, ActionTaskResultAdmin)
