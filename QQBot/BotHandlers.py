#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年10月22日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: QQBot.BotHandlers
@description: 
"""
import json
import logging

from tornado.escape import to_basestring
from tornado.gen import coroutine
from tornado.web import RequestHandler

from QQBot.BotInterface import MessageInQueue, DottedDict


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'
__Version__ = 1.0

Handlers = []


class IndexHandler(RequestHandler):

    @coroutine
    def get(self, *args, **kwargs):  # @UnusedVariable
        self.finish({'msg': 'ok'})


class MessageHandler(RequestHandler):

    def prepare(self):
        super(MessageHandler, self).prepare()
        if self.request.body:
            try:
                self._data = json.loads(
                    to_basestring(self.request.body), object_hook=DottedDict)
            except Exception as e:
                logging.exception(e)
        else:
            self._data = DottedDict()

    @coroutine
    def post(self, *args, **kwargs):  # @UnusedVariable
        # 把消息放入队列
        yield MessageInQueue.put(self._data)
        self.finish({'msg': 'ok'})
