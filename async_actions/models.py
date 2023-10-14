from django_celery_results.models import TaskResult
from item_messages.constants import DEFAULT_TAGS
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db import models
from django.utils.translation import gettext_lazy as _
from .exceptions import OccupiedLockException


class ActionTaskState(TaskResult):
    """
    _summary_
    """

    ctype = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    obj_id = models.PositiveIntegerField()
    obj = GenericForeignKey("ctype", "obj_id")

    class Meta:
        indexes = (
            models.Index(fields=["obj_id"]),
            models.Index(fields=["ctype"]),
        )


class ActionTaskNote(models.Model):
    """
    _summary_
    """

    action_task = models.ForeignKey(
        ActionTaskState,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("AktionTaskResult"),
        help_text=_("AktionTaskResult"),
    )
    level = models.CharField(
        max_length=128,
        choices=[(k, v) for k, v in DEFAULT_TAGS.items()],
        default='info',
        verbose_name=_("Message-level"),
        help_text=_("Level with which the message were added."),
    )
    note = models.TextField(
        verbose_name=_("Note"),
        help_text=_("ActionTask note"),
    )
    created_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Time of creation"),
        help_text=_("The datetime this message were added."),
    )

    @property
    def level_tag(self):
        return DEFAULT_TAGS.get(int(self.level), "")

    class Meta:
        ordering = ("action_task", "created_time")
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")


class LockManager(models.Manager):
    """
    _summary_
    """
    @transaction.atomic
    def get_locks(self, *lock_ids):
        r"""
        _summary_

        :param list \*lock_ids: ids of locks to be released
        :return _type_: _description_
        """
        for lock_id in lock_ids:
            _, created = self.get_or_create(checksum=lock_id)
            if not created:
                raise OccupiedLockException(lock_id)
        return lock_ids

    def release_locks(self, *lock_ids):
        r"""
        Release locks by deleting their :class:`~.models.Lock` instances.

        :param list \*lock_ids: ids of locks to be released
        """
        for lock_id in lock_ids:
            self.get(checksum=lock_id).delete()


class Lock(models.Model):
    """
    Very simple lock mechanism based on a unique checksum.

    # TODO: Using https://github.com/nshafer/django-hashid-field/ might be a
    more reliable alternative.
    """
    checksum = models.CharField('Checksum', max_length=24, unique=True)
    objects = LockManager()
