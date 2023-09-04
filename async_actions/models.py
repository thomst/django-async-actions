from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models



class ObjectTaskState(models.Model):
    """
    _summary_
    """
    task_id = models.CharField(max_length=128, unique=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    obj = GenericForeignKey("content_type", "object_id")
    created_time = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(null=True)

    def save(self, *args, **kwargs):
        # active must be None or True.
        if not self.active:
            self.active = None
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('content_type', 'object_id', 'active')
        ordering = ('-created_time',)
        indexes = (
            models.Index(fields=["task_id"]),
        )
