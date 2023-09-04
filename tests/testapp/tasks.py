import time
from celery import shared_task


@shared_task(bind=True)
def test_task(self, context):
    context.add_note('NoteOne')

    time.sleep(2)
    context.add_note('NoteTwo')

    time.sleep(4)
    context.add_note('NoteThree')

    time.sleep(6)
    context.add_note('NoteFour')
