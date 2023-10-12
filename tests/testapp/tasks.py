import time
from celery import shared_task
from celery.canvas import chain


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
def task_with_kwargs(self, *args, **kwargs):
    self.add_note(f'NoteOne for {self.obj}')
    # self.add_note(f'This task was called with {args}')
    self.add_note(f'This task was called with {kwargs}')


@shared_task(bind=True)
def task_that_fails(self):
    self.add_note(f'NoteOne for {self.obj}')
    raise Exception('Buuhhhhhh')


@shared_task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


test_chain = task_with_kwargs.s(foo='bar') | task_with_kwargs.s(fooo='bar')
test_chain = test_task.si() | test_task.si()
