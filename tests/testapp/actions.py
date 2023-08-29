import time
from celery import group
from celery.result import AsyncResult
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render

from item_messages.api import info
from item_messages.api import add_message
from .forms import MessageFrom
from .tasks import test_task


def add_messages(modeladmin, request, queryset):
    if 'add_messages' in request.POST:
        form = MessageFrom(request.POST)
    else:
        form = MessageFrom()

    if form.is_valid():
        # add message
        data = form.cleaned_data
        for obj in queryset.all():
            add_message(request, data['level'], obj, data['message'])

        return HttpResponseRedirect(request.get_full_path())
    else:
        return render(request, 'testapp/message.html', {
            'objects': queryset.order_by('pk'),
            'form': form,
            })


def run_test_task(modeladmin, request, queryset):
    results = dict()
    signatures = list()
    for obj in queryset.all():
        ct = ContentType.objects.get_for_model(type(obj))
        signature = test_task.si((ct.id, obj.id))
        signature.freeze()
        info(request, obj, f'{signature.id}')
        signatures.append(signature)

    results = group(*signatures).delay()

    # for result in results:
    #     print(AsyncResult(result.task_id).state)

    # print('-------------')

    # time.sleep(1)
    # for result in results:
    #     print(AsyncResult(result.task_id).state)
    # print('-------------')

    # time.sleep(2)
    # for result in results:
    #     print(AsyncResult(result.task_id).state)
