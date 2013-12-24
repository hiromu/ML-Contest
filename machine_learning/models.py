# -*- coding: utf-8 -*-

import uuid

from django.db.models import BooleanField, CharField, CommaSeparatedIntegerField, DateTimeField, FileField, FloatField, ForeignKey, ManyToManyField, Model, PositiveIntegerField, TextField

def random_path(instance, filename):
    return str(uuid.uuid4())

class Problem(Model):
    name = CharField(u'タイトル', max_length = 60)
    statement = TextField(u'本文')
    traindata = FileField(u'学習データ', upload_to = random_path)
    testdata = FileField(u'テストデータ', upload_to = random_path)
    count = PositiveIntegerField(u'テストデータの数')
    type = PositiveIntegerField(u'スコア算出方法')
    threshold = FloatField(u'閾値')
    coefficient = FloatField(u'係数')
    score = FloatField(u'スコア')
    size = PositiveIntegerField()

class Submission(Model):
    user = ForeignKey('auth.User')
    problem = ForeignKey(Problem)
    score = FloatField(u'スコア', default = 0)
    data = FileField(u'回答', upload_to = random_path, null = True)
    source = FileField(u'ソースコード', upload_to = random_path, null = True)
    testcase = CommaSeparatedIntegerField(max_length = 100000)
    datetime = DateTimeField()
