#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年10月22日
@author: Irony
@site: https://pyqt.site https://github.com/892768447
@email: 892768447@qq.com
@file: QQBots.BotHandlers
@description: 
"""
import json
import logging
from urllib.parse import quote

from tornado.escape import to_basestring
from tornado.gen import coroutine
from tornado.web import RequestHandler, HTTPError, authenticated

from QQBots.BotInterface import MessageInQueue, DottedDict


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'
__Version__ = 1.0


class BaseHandler(RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie('username')


class IndexHandler(BaseHandler):

    @coroutine
    @authenticated
    def get(self, *args, **kwargs):  # @UnusedVariable
        self.finish({'msg': 'ok'})


class NotFoundHandler(BaseHandler):

    @coroutine
    def get(self, *args, **kwargs):  # @UnusedVariable
        self.set_status(404)
        self.render('404.html')


class LoginHandler(BaseHandler):

    @coroutine
    def get(self, *args, **kwargs):
        self.render('login.html', next=quote(self.get_argument('next', '/')))

    @coroutine
    def post(self, *args, **kwargs):
        username = self.get_argument('username')
        password = self.get_argument('password')
        self.set_secure_cookie('username', username)
        self.redirect(self.get_argument('next', '/'))


class MessageHandler(BaseHandler):

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
