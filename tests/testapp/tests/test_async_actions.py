from django.test import TestCase
from testapp.management.commands.createtestdata import create_test_data



class ItemMessagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def test_01(self):
        pass