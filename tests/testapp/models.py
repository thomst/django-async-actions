# -*- coding: utf-8 -*-

from django.db import models


class TestModel(models.Model):
    one = models.CharField(max_length=128, blank=True, null=True)
    two = models.CharField(max_length=128, blank=True, null=True)
    three = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        ordering = ['id']