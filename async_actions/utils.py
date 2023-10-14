import hashlib


def get_object_checksum(obj):
    """
    _summary_

    :param _type_ obj: _description_
    """
    seed = f'{obj.id}-{type(obj).__name__}-{type(obj).__module__}'
    hash_ = hashlib.shake_128(seed.encode())
    return hash_.hexdigest(12)
