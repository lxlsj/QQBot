#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年9月2日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: MsgHandler
@description: 
"""
from tornado.gen import coroutine

from BotInterface import Interface


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019 Irony'
__Version__ = 1.0


@coroutine
def _send_message(message):
    """发送队列消息
    :param message:
    """


@coroutine
def _recv_message(message):
    """接收队列消息
    :param message:
    """
    message = Interface.getMsgInfo(message)
    print(message)
