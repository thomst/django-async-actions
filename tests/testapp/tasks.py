import time
from celery import shared_task


@shared_task(bind=True)
def test_task(self, context):
    self.add_note('NoteOne')

    time.sleep(2)
    self.add_note('NoteTwo')

    time.sleep(4)
    self.add_note('NoteThree')

    time.sleep(6)
    self.add_note('NoteFour')
