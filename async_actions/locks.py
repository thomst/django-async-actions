
import hashlib
from .models import Lock


def get_object_lock(obj):
    """
    Set one or multiple locks for a :class:`~django.db.models.Model` instance.

    :param :class:`~django.db.models.Model` obj: any kind of Model instance
    :return tuple: tuple of lock-ids
    :raise OccupiedLockException: if the lock couldn't be achieved
    """
    seed = f'{obj.id}-{type(obj).__name__}-{type(obj).__module__}'
    hash_ = hashlib.shake_128(seed.encode())
    lock_id = hash_.hexdigest(12)
    return Lock.objects.get_lock(lock_id)


def release_locks(*lock_ids):
    r"""
    Release locks by deleting their :class:`~.models.Lock` instances.

    :param list \*lock_ids: ids of locks to be released
    """
    for lock_id in lock_ids:
        Lock.objects.get(checksum=lock_id).delete()
