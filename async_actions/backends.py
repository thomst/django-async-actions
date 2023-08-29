from django_celery_results.backends import DatabaseBackend
from .models import ActionTaskResult


class ActionDatabaseBackend(DatabaseBackend):
    """
    _summary_
    """
    TaskModel = ActionTaskResult
