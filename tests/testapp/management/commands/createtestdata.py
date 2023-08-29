# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from testapp.models import TestModel


def create_test_data():
    # create admin-user
    User.objects.all().delete()
    user = User.objects.create_superuser('admin', 'admin@testapp.de', 'adminpassword')

    # clear existing data
    TestModel.objects.all().delete()

    items = list()
    for i in range(12):
        item = TestModel()
        item.one = 'one'
        item.two = 'two'
        item.three = 'three'
        item.save()
        items.append(item)


class Command(BaseCommand):
    help = 'Create test data.'

    def handle(self, *args, **options):
        create_test_data()
