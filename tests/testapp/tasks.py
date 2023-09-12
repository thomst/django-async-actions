import time
from celery import shared_task


@shared_task(bind=True)
def test_task(self, obj):
    self.add_note(f'NoteOne for {obj}')

    time.sleep(2)
    self.add_note(f'NoteTwo for {obj}')

    time.sleep(4)
    self.add_note(f'NoteThree for {obj}')

    time.sleep(6)
    self.add_note(f'NoteFour for {obj}')
