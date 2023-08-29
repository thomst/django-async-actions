import time
from celery import shared_task


@shared_task(bind=True)
def test_task(self, obj):
    print(f'[{self.request.id}][{obj.id}] Request: {self.request!r}')
    self.add_note('NoteOne')

    time.sleep(2)
    now = time.time()
    print(f'[{self.request.id}][{obj.id}] {now}')
    self.add_note('NoteTwo')
    # self.update_state(state='PROGRESS', meta=dict(time=now))
