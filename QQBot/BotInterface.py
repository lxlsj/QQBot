#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年10月24日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: QQBot.BotInterface
@description: 
"""
from tornado.queues import Queue


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'
__Version__ = 1.0

# 待处理消息队列
MessageInQueue = Queue()
# 待发送消息队列
MessageOutQueue = Queue()

DefaultHeaders = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6824.400 QQBrowser/10.3.3137.400'
}