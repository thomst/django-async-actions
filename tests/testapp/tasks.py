import time
from celery import shared_task


@shared_task(bind=True)
def test_task(self, obj):
    self.add_note(f'NoteOne for {obj}')

    time.sleep(1)
    self.add_note(f'NoteTwo for {obj}')

    time.sleep(1)
    self.add_note(f'NoteThree for {obj}')

    time.sleep(1)
    self.add_note(f'NoteFour for {obj}')


@shared_task(bind=True)
def task_with_arg(self, obj, arg):
    self.add_note(f'NoteOne for {obj}')
    self.add_note(f'This task was called with {arg}')


@shared_task(bind=True)
def task_with_kwargs(self, obj, **kwargs):
    self.add_note(f'NoteOne for {obj}')
    self.add_note(f'This task was called with {kwargs}')


@shared_task(bind=True)
def task_that_fails(self, obj):
    self.add_note(f'NoteOne for {obj}')
    raise Exception('Buuhhhhhh')
