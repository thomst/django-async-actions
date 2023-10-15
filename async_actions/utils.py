import hashlib
import celery


def get_object_checksum(obj):
    """
    _summary_

    :param _type_ obj: _description_
    """
    seed = f'{obj.id}-{type(obj).__name__}-{type(obj).__module__}'
    hash_ = hashlib.shake_128(seed.encode())
    return hash_.hexdigest(12)


def get_task_message_checksum(task_state):
    """
    _summary_

    :param _type_ task_state: _description_
    :return _type_: _description_
    """
    if task_state.status == celery.states.RETRY:
        seed = f'{task_state.traceback.splitlines()[-1]}'
    else:
        # TODO: Do we hit the database with count() if notes are preloaded?
        seed = f'{task_state.status}{task_state.notes.count()}'
    hash_ = hashlib.shake_128(seed.encode())
    return hash_.hexdigest(12)
