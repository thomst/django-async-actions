import time
from celery import shared_task
from celery import group


@shared_task(bind=True)
def test_task(self):
    self.add_note(f'Test task run with {self.obj}')


@shared_task(bind=True)
def long_running_task(self):
    self.add_note(f'NoteOne for {self.obj}')

    time.sleep(2)
    self.add_note(f'NoteTwo for {self.obj}')

    time.sleep(2)
    self.add_note(f'NoteThree for {self.obj}')

    time.sleep(2)
    self.add_note(f'NoteFour for {self.obj}')


@shared_task(bind=True, verbose_name='Info Task')
def info_task(self):
    self.add_note(f'self.obj: {self.obj}')
    self.add_note(f'self.state: {self.state}')
    self.add_note(f'self._lock_ids: {self._lock_ids}')
    self.add_note(f'self.request.id: {self.request.id}')


@shared_task(bind=True)
def task_with_arg(self, arg):
    self.add_note(f'This task was called with {arg}')


@shared_task(bind=True)
def task_with_kwargs(self, **kwargs):
    self.add_note(f'This task was called with {kwargs}')


@shared_task(bind=True)
def task_that_fails(self):
    self.add_note(f'NoteOne for {self.obj}')
    raise Exception('Buuhhhhhh')


@shared_task(bind=True)
def task_that_calls_other_tasks(self):
    self.add_note(f'self.obj: {self.obj}')
    self.add_note(f'self.state: {self.state}')
    self.add_note(f'self._lock_ids: {self._lock_ids}')
    self.add_note(f'self.request.id: {self.request.id}')
    debug_task.run_with(self.state)()
    info_task.run_with(self.state)()
    task_that_fails.run_with(self.state)()


@shared_task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


test_chain = info_task.si() | task_with_kwargs.si(fooo='bar')
test_chain_that_fails = info_task.si() | task_that_fails.si() | task_with_kwargs.s(fooo='bar')
test_group = group(debug_task.si(), debug_task.si(), debug_task.si())
test_group_that_fails = group(debug_task.si(), debug_task.si(), task_that_fails.si())
test_chord = (group(debug_task.si(), debug_task.si()) | task_with_arg.s())
test_chord_with_failing_callback = (group(debug_task.si(), debug_task.si()) | task_that_fails.si())
test_chord_with_failing_group = (group(debug_task.si(), task_that_fails.si()) | debug_task.si())
