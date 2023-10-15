from django.contrib.auth.models import User
from .models import TestModel


def create_test_data():
    # create admin-user
    User.objects.all().delete()
    User.objects.create_superuser('admin', 'admin@testapp.de', 'adminpassword')

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
