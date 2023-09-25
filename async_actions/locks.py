
from .models import Lock


def get_object_lock(obj):
    """
    Set one or multiple locks for a :class:`~django.db.models.Model` instance.

    :param :class:`~django.db.models.Model` obj: any kind of Model instance
    :return tuple: tuple of lock-ids
    :raise OccupiedLockException: if the lock couldn't be achieved
    """
    lock_id = hash((obj.id, type(obj).__name__, type(obj).__module__))
    Lock.objects.get_lock(lock_id)
    return lock_id


def release_locks(*lock_ids):
    r"""
    Release locks by deleting their :class:`~.models.Lock` instances.

    :param list \*lock_ids: ids of locks to be released
    """
    for lock_id in lock_ids:
        Lock.objects.get(checksum=int(lock_id)).delete()
