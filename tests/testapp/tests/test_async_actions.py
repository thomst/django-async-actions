import json
import urllib
from unittest.mock import patch
from unittest.mock import Mock
import celery
from celery.canvas import group
from celery.canvas import _chain
from celery.canvas import Signature
import item_messages
from item_messages.middleware import ItemMessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.test import RequestFactory
from testapp.models import TestModel
from testapp.tasks import test_task
from testapp.tasks import test_chain
from testapp.utils import create_test_data
from async_actions import __version__
from async_actions.models import Lock
from async_actions.models import ActionTaskState
from async_actions.tasks import ActionTask
from async_actions.tasks import get_locks
from async_actions.tasks import release_locks
from async_actions.tasks import release_locks_on_error
from async_actions.exceptions import OccupiedLockException
from async_actions.messages import build_task_message
from async_actions.messages import add_task_message
from async_actions.utils import get_task_message_checksum
from async_actions.utils import get_task_name
from async_actions.utils import get_task_verbose_name
from async_actions.utils import get_task_description
from async_actions.views import update_task_messages
from async_actions.processor import Processor
from async_actions.actions import as_action
from async_actions.actions import TaskAction


class AsyncActionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.get(username='admin')
        get_response = Mock()
        self.session_middleware = SessionMiddleware(get_response)
        self.messages_middleware = ItemMessageMiddleware(get_response)


    def create_task_state(self):
        obj = TestModel.objects.get(pk=1)
        content_type = ContentType.objects.get_for_model(type(obj))
        params = dict(
            ctype=content_type,
            obj_id=obj.pk,
            task_id='dummy-task-id',
            task_name='testapp.tasks.dummy_task',
            verbose_name='Dummy task',
            status=celery.states.PENDING
        )
        task_state = ActionTaskState(**params)
        task_state.save()
        return task_state

    def get_request(self, url):
        request = self.factory.get(url)
        self.session_middleware.process_request(request)
        self.messages_middleware.process_request(request)
        request.user = self.user
        return request

    def test_lock(self):
        # Create a simple lock.
        lock_id = 'mylock'
        lock = Lock(checksum=lock_id)
        lock.save()

        # See if occupied lock exception is raised.
        with self.assertRaises(OccupiedLockException):
            Lock.objects.get_locks(lock_id)

        lock_ids = ['firstlock', lock_id, 'anotherlock']
        # This should also work with two or more lock ids.
        with self.assertRaises(OccupiedLockException):
            Lock.objects.get_locks(*lock_ids)

        # Afterwards no new lock must have been created.
        with self.assertRaises(Lock.DoesNotExist):
            Lock.objects.get(checksum=lock_ids[0])

        with self.assertRaises(Lock.DoesNotExist):
            Lock.objects.get(checksum=lock_ids[-1])

        # Create some other locks and release them.
        lock_ids = ['firstlock', 'secondlock']
        Lock.objects.get_locks(*lock_ids)
        locks = Lock.objects.filter(checksum__in=lock_ids)
        self.assertEqual(len(locks), len(lock_ids))
        Lock.objects.release_locks(locks[0].checksum, locks[1].checksum)
        with self.assertRaises(Lock.DoesNotExist):
            Lock.objects.get(checksum=lock_ids[0])
        with self.assertRaises(Lock.DoesNotExist):
            Lock.objects.get(checksum=lock_ids[1])

    def test_lock_tasks(self):
        lock_ids = ['lock_one', 'lock_two']
        get_locks(*lock_ids)
        self.assertEqual(Lock.objects.filter(checksum__in=lock_ids).count(), len(lock_ids))

        # Use release_locks task to delete locks.
        release_locks(*lock_ids)
        self.assertEqual(Lock.objects.filter(checksum__in=lock_ids).count(), 0)

        # Test release_locks_on_error.
        get_locks(*lock_ids)

        # Called with an instance of OccupiedLockException the locks shouldn't
        # be released.
        release_locks_on_error(Mock(), OccupiedLockException(), Mock(), *lock_ids)
        self.assertEqual(Lock.objects.filter(checksum__in=lock_ids).count(), len(lock_ids))

        # Called with another Exception they should be released.
        release_locks_on_error(Mock(), Exception(), Mock(), *lock_ids)
        self.assertEqual(Lock.objects.filter(checksum__in=lock_ids).count(), 0)

    def test_build_task_messages(self):
        task_state = self.create_task_state()
        level, msg, tag, data = build_task_message(task_state)
        self.assertEqual(level, item_messages.INFO)
        self.assertTrue(task_state.status in msg)
        self.assertTrue(task_state.task_id in msg)
        self.assertTrue(task_state.verbose_name in msg)
        self.assertEqual(tag, 'task-waiting')
        self.assertEqual(data['task_id'], task_state.task_id)
        self.assertEqual(data['checksum'], get_task_message_checksum(task_state))

        task_state.status = celery.states.STARTED
        level, msg, tag, data = build_task_message(task_state)
        self.assertEqual(level, item_messages.INFO)
        self.assertTrue(task_state.status in msg)

        task_state.status = celery.states.SUCCESS
        level, msg, tag, data = build_task_message(task_state)
        self.assertEqual(level, item_messages.INFO)
        self.assertTrue(task_state.status in msg)

        task_state.status = celery.states.FAILURE
        level, msg, tag, data = build_task_message(task_state)
        self.assertEqual(level, item_messages.ERROR)
        self.assertTrue(task_state.status in msg)

    def test_update_task_messages_view(self):
        # Create task and message to have a msg_id.
        task_state = self.create_task_state()
        url = reverse('admin:testapp_testmodel_changelist')
        request = self.get_request(url)
        msg_id = add_task_message(request, task_state)

        # Now we call our update messages view.
        params = {
            task_state.task_id: {
                'msg_id': msg_id,
                'checksum': get_task_message_checksum(task_state),
            }
        }
        url_params = urllib.parse.urlencode(dict(msgs=json.dumps(params)))
        url = f'/async_actions/update_task_messages/?{url_params}'

        request = self.get_request(url)
        msg_id = add_task_message(request, task_state)
        response = update_task_messages(request)
        messages = json.loads(response.content.decode())

        # Since we did not alter the task_state no message should have been
        # updated.
        self.assertDictEqual(messages, {})

        # Lets change the task_state and try it again.
        request = self.get_request(url)
        msg_id = add_task_message(request, task_state)
        task_state.status = celery.states.STARTED
        task_state.save()
        response = update_task_messages(request)
        messages = json.loads(response.content.decode())
        self.assertIn(msg_id, messages)

        # Test message with RETRY state.
        # First update task and call the view with the original checksum.
        request = self.get_request(url)
        msg_id = add_task_message(request, task_state)
        task_state.status = celery.states.RETRY
        task_state.traceback = 'Last line of traceback.'
        task_state.save()
        response = update_task_messages(request)
        messages = json.loads(response.content.decode())
        self.assertIn(msg_id, messages)

        # Then update the the checksum passed as get params.
        params[task_state.task_id]['checksum'] = get_task_message_checksum(task_state)
        url_params = urllib.parse.urlencode(dict(msgs=json.dumps(params)))
        url = f'/async_actions/update_task_messages/?{url_params}'
        request = self.get_request(url)
        msg_id = add_task_message(request, task_state)
        response = update_task_messages(request)
        messages = json.loads(response.content.decode())
        self.assertDictEqual(messages, {})

        # Now Update the traceback and see if the message will be updated by our
        # view.
        request = self.get_request(url)
        msg_id = add_task_message(request, task_state)
        task_state.traceback = 'Another last traceback line.'
        task_state.save()
        response = update_task_messages(request)
        messages = json.loads(response.content.decode())
        self.assertIn(msg_id, messages)

    def test_processor(self):
        # Initialize a processor.
        queryset = TestModel.objects.all()
        signature = test_task.si()
        processor = Processor(queryset, signature)
        workflow = processor.workflow
        self.assertIsInstance(workflow, group)
        self.assertEqual(type(processor.signatures[0]), Signature)
        task_states = ActionTaskState.objects.all()
        self.assertEqual(set(task_states), set([l[0] for l in processor.task_states]))
        self.assertEqual(set(t.task_id for t in task_states), set(s.id for s in processor.signatures))

        # Just for the coverage...
        with patch.object(processor.workflow, 'delay'):
            processor.run()
            processor.results

    def test_processor_with_outer_lock(self):
        # Initialize a processor with Processor.OUTER_LOCK.
        queryset = TestModel.objects.all()
        signature = test_task.si()
        processor = Processor(queryset, signature, lock_mode=Processor.OUTER_LOCK)
        workflow = processor.workflow
        self.assertIsInstance(workflow, group)
        self.assertEqual(type(processor.signatures[0]), _chain)
        task_states = ActionTaskState.objects.all()
        self.assertEqual(set(task_states), set([t for l in processor.task_states for t in l]))
        self.assertEqual(set(t.task_id for t in task_states), set(t.id for s in processor.signatures for t in s.tasks))

    def test_processor_with_chain(self):
        # Initialize a processor with a chain as signature.
        queryset = TestModel.objects.all()
        processor = Processor(queryset, test_chain)
        workflow = processor.workflow
        self.assertIsInstance(workflow, group)
        self.assertEqual(type(processor.signatures[0]), _chain)
        task_states = ActionTaskState.objects.all()
        self.assertEqual(set(task_states), set([t for l in processor.task_states for t in l]))
        self.assertEqual(set(t.task_id for t in task_states), set(t.id for s in processor.signatures for t in s.tasks))

    def test_processor_with_chain_and_outer_lock(self):
        # Initialize a processor with a chain as signature and Processor.OUTER_LOCK.
        queryset = TestModel.objects.all()
        processor = Processor(queryset, test_chain, lock_mode=Processor.OUTER_LOCK)
        workflow = processor.workflow
        self.assertIsInstance(workflow, group)
        self.assertEqual(type(processor.signatures[0]), _chain)
        task_states = ActionTaskState.objects.all()
        self.assertEqual(set(task_states), set([t for l in processor.task_states for t in l]))
        self.assertEqual(set(t.task_id for t in task_states), set(t.id for s in processor.signatures for t in s.tasks))

    def test_action_task(self):
        task_state = self.create_task_state()
        test_task.request.update(id=task_state.task_id)

        # Test ActionTask properties.
        self.assertEqual(test_task.state, task_state)
        self.assertEqual(test_task.obj, task_state.obj)
        self.assertEqual(test_task.notes, task_state.notes)

        # Add a note.
        test_task.add_note('foobar')
        self.assertEqual(test_task.notes.all().count(), 1)
        self.assertEqual(test_task.notes.all()[0].note, 'foobar')

        # Just call the run_with method.
        self.assertEqual(test_task, test_task.run_with(task_state))

        # Test locking mechanism via before_start method without lock-ids.
        test_task.before_start(task_state.task_id, [], {})
        self.assertIsNone(test_task._lock_ids)

        # Now create locks and pass in the lock-ids to request.headers.
        lock_ids = ['lock_one', 'lock_two']
        test_task.request.headers = dict(lock_ids=lock_ids)
        test_task.before_start(task_state.task_id, [], {})
        self.assertEqual(test_task._lock_ids, lock_ids)
        self.assertEqual(Lock.objects.filter(checksum__in=lock_ids).count(), len(lock_ids))

        # Now that the locks are created a get_locks call should trigger a retry.
        test_task.retry = Mock(spec=ActionTask.retry)
        test_task.get_locks(*lock_ids)
        test_task.retry.assert_called_once()
        self.assertIsInstance(test_task.retry.call_args[1]['exc'], OccupiedLockException)
        self.assertIsInstance(test_task.retry.call_args[1]['countdown'], int)
        self.assertEqual(test_task.retry.call_args[1]['max_retries'], test_task.locked_max_retries)

        # Run get_locks again with locked_retry_backoff = None
        test_task.retry = Mock(spec=ActionTask.retry)
        test_task.locked_retry_backoff = None
        test_task.get_locks(*lock_ids)
        test_task.retry.assert_called_once()
        self.assertIsInstance(test_task.retry.call_args[1]['exc'], OccupiedLockException)
        self.assertEqual(test_task.retry.call_args[1]['countdown'], test_task.locked_retry_delay)
        self.assertEqual(test_task.retry.call_args[1]['max_retries'], test_task.locked_max_retries)

        # Release the locks via after_return method.
        test_task.after_return(Mock(), Mock(), Mock(), Mock(), Mock(), Mock())
        self.assertEqual(Lock.objects.filter(checksum__in=lock_ids).count(), 0)

    def test_get_task_verbose_name(self):
        # Test verbose_name derivation.
        orig_verbose_name = 'foobar'

        # No verbose name specified it will be derived from the function name.
        def func_one(): pass
        my_task = celery.shared_task(func_one)
        verbose_name = get_task_verbose_name(my_task.si())
        self.assertEqual(
            verbose_name.replace(' ', '').lower(),
            func_one.__name__.replace('_', '').lower())

        # Verbose name specified on task.
        def func_two(): pass
        my_task = celery.shared_task(func_two)
        my_task.verbose_name = orig_verbose_name
        verbose_name = get_task_verbose_name(my_task.si())
        self.assertEqual(orig_verbose_name, verbose_name)

        # Verbose name specified on signature.
        def func_three(): pass
        my_task = celery.shared_task(func_three)
        my_sig = my_task.si()
        my_sig.verbose_name = orig_verbose_name
        verbose_name = get_task_verbose_name(my_sig)
        self.assertEqual(orig_verbose_name, verbose_name)

        # Verbose name for canvas.
        def func_four(): pass
        my_task = celery.shared_task(func_four)
        my_chain = my_task.si() | my_task.si()
        verbose_name = get_task_verbose_name(my_chain)
        self.assertEqual(repr(my_chain)[:56], verbose_name[:56])

        # Verbose name for canvas explicitly specified.
        def func_five(): pass
        my_task = celery.shared_task(func_five)
        my_chain = my_task.si() | my_task.si()
        my_chain.verbose_name = orig_verbose_name
        verbose_name = get_task_verbose_name(my_chain)
        self.assertEqual(orig_verbose_name, verbose_name)

    def test_get_task_description(self):
        # Test description derivation.
        orig_description = 'foobar'

        # No description specified.
        def func_one(): pass
        my_task = celery.shared_task(func_one)
        description = get_task_description(my_task.si())
        self.assertFalse(description)

        # Description specified on task.
        def func_two(): pass
        my_task = celery.shared_task(func_two)
        my_task.description = orig_description
        description = get_task_description(my_task.si())
        self.assertEqual(orig_description, description)

        # Description specified on signature.
        def func_three(): pass
        my_sig = celery.shared_task(func_three).si()
        my_sig.description = orig_description
        description = get_task_description(my_sig)
        self.assertEqual(orig_description, description)

        # Description specified as docstring.
        def func_four(): pass
        func_four.__doc__ = orig_description
        my_task = celery.shared_task(func_four)
        my_sig = my_task.si()
        description = get_task_description(my_sig)
        self.assertEqual(orig_description, description)

        # Description for canvas.
        def func_five(): pass
        my_task = celery.shared_task(func_five)
        my_chain = my_task.si() | my_task.si()
        description = get_task_description(my_chain)
        self.assertEqual(repr(my_chain), description)

        # Description for canvas explicitly specified.
        def func_six(): pass
        my_task = celery.shared_task(func_six)
        my_chain = my_task.si() | my_task.si()
        my_chain.description = orig_description
        description = get_task_description(my_chain)
        self.assertEqual(orig_description, description)

    def test_as_action_decorator(self):
        # Use as_action with task.
        def func_one(): pass
        my_task = celery.shared_task(func_one)
        task_action = as_action(my_task)
        self.assertIsInstance(task_action, TaskAction)

        # Use as_action with signature.
        def func_two(): pass
        my_task = celery.shared_task(func_two)
        task_action = as_action(my_task.si())
        self.assertIsInstance(task_action, TaskAction)

        # Use as_action decorator
        @as_action
        @celery.shared_task
        def func_three(): pass
        self.assertIsInstance(func_three, TaskAction)

        # Use as_action decorator with arguments
        @as_action(lock_mode=Processor.OUTER_LOCK)
        @celery.shared_task
        def func_four(): pass
        self.assertIsInstance(func_four, TaskAction)
        self.assertEqual(Processor.OUTER_LOCK, func_four._lock_mode)

        # Use as_action with verbose_name and description.
        def func_five(): pass
        my_task = celery.shared_task(func_five)
        task_action = as_action(my_task, verbose_name='foobar', description='foobar')
        self.assertEqual(task_action.short_description, 'foobar')
        self.assertEqual(task_action.description, 'foobar')
        self.assertEqual(task_action._sig.verbose_name, 'foobar')
        self.assertEqual(task_action._sig.description, 'foobar')
