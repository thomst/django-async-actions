
import hashlib
from django.db import transaction
from .models import Lock


def get_object_checksum(obj):
    """
    _summary_

    :param _type_ obj: _description_
    """
    seed = f'{obj.id}-{type(obj).__name__}-{type(obj).__module__}'
    hash_ = hashlib.shake_128(seed.encode())
    return hash_.hexdigest(12)


@transaction.atomic
def get_locks(*lock_ids):
    """
    _summary_

    :return _type_: _description_
    """
    locks = []
    for lock_id in lock_ids:
        locks.append(Lock.objects.get_lock(lock_id))
    return locks


def release_locks(*lock_ids):
    r"""
    Release locks by deleting their :class:`~.models.Lock` instances.

    :param list \*lock_ids: ids of locks to be released
    """
    for lock_id in lock_ids:
        Lock.objects.get(checksum=lock_id).delete()
