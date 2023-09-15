import time
from celery import shared_task


@shared_task(bind=True)
def test_task(self):
    self.add_note(f'NoteOne for {self.obj}')

    time.sleep(2)
    self.add_note(f'NoteTwo for {self.obj}')

    time.sleep(2)
    self.add_note(f'NoteThree for {self.obj}')

    time.sleep(2)
    self.add_note(f'NoteFour for {self.obj}')


@shared_task(bind=True)
def task_with_arg(self, arg):
    self.add_note(f'NoteOne for {self.obj}')
    self.add_note(f'This task was called with {arg}')


@shared_task(bind=True)
def task_with_kwargs(self, **kwargs):
    self.add_note(f'NoteOne for {self.obj}')
    self.add_note(f'This task was called with {kwargs}')


@shared_task(bind=True)
def task_that_fails(self):
    self.add_note(f'NoteOne for {self.obj}')
    raise Exception('Buuhhhhhh')
