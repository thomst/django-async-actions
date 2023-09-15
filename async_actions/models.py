from kombu.serialization import loads
from django_celery_results.models import TaskResult
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models



class ActionTaskResult(TaskResult):
    """
    _summary_
    """

    ctype = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    obj_id = models.PositiveIntegerField()
    obj = GenericForeignKey("ctype", "obj_id")
    active = models.BooleanField(null=True)

    @property
    def state_hash(self):
        return hash((self.status, self.result))

    def get_meta_data(self):
        return loads(self.result, self.content_type, self.content_encoding)

    def save(self, *args, **kwargs):
        # active must be None or True to be useful in a unique-together context.
        if not self.active:
            self.active = None
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("ctype", "obj_id", "active")
        indexes = (
            models.Index(fields=["obj_id"]),
            models.Index(fields=["ctype"]),
        )
