

def get_message_checksum(task):
    """
    A checksum indicating an updated message.
    """
    return hash((task.status, task.notes.values_list('id', flat=True)))
