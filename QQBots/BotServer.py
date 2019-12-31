#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年10月23日
@author: Irony
@site: https://pyqt.site https://github.com/892768447
@email: 892768447@qq.com
@file: QQBots.BotServer
@description: 
"""

import base64
import json
import logging
import os

import colorama
from tornado.escape import to_basestring
from tornado.gen import coroutine, sleep
from tornado.httpclient import HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define
from tornado.options import options
from tornado.web import Application
from tornado.websocket import websocket_connect

from QQBots import BotInterface
from QQBots.BotHandlers import MessageHandler, IndexHandler, LoginHandler
from QQBots.BotInterface import MessageOutQueue, MessageInQueue, Interface,\
    DottedDict


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'
__Version__ = 1.0

define('host', default='0.0.0.0',
       metavar='0.0.0.0 或者 127.0.0.1', help='服务端绑定地址')
define('port', default=52610, help='服务端绑定端口')
define('delay', default=0.01, type=float, help='消息队列的休眠时间')

# 酷Q
define('cqhost', type=str, default='127.0.0.1',
       metavar='127.0.0.1 或者 其它远程地址',
       help='酷Q 插件客户端监听地址，比如127.0.0.1 或者 其它远程地址')
define('cqport', type=int, default=52611,
       help='酷Q 插件客户端监听端口, 需要在插件中自行设置\n见CQA/app/io.github.richardchien.coolqhttpapi/config.cfg')

# QQLight
define('qlhost', type=str, default='127.0.0.1',
       metavar='127.0.0.1 或者 其它远程地址',
       help='QQLight 插件客户端监听地址，比如127.0.0.1 或者 其它远程地址')
define('qlport', type=int, default=52612,
       help='QQLight 插件客户端监听端口, 需要在插件中自行设置\n见QQLight/plugin/websocket.protocol/config.json')

# 契约
define('qyhost', type=str, default='127.0.0.1',
       metavar='127.0.0.1 或者 其它远程地址',
       help='契约 插件客户端监听地址，比如127.0.0.1 或者 其它远程地址')
define('qyport', type=int, default=52613,
       help='契约 插件客户端监听端口, 需要在插件中自行设置\n见QyBot/PC/plugin/com.tayuyu.http/你的QQ号.json文件\n新建你的QQ号.json内容为：{"port":"52613","urlList":["http://127.0.0.1:52610/message"]}')


log = logging.getLogger('tornado.general')


class BotApplication(Application):

    def __init__(self, *args, **kwargs):
        # 扩展路由
        handlers = [
            (r'/message', MessageHandler),
            (r'/login', LoginHandler)
            (r'.*', IndexHandler)
        ]
        dirpath = os.path.dirname(BotInterface.__file__)
        settings = {
            'debug': False,
            'compiled_template_cache': False,  # 关闭模板缓存
            'static_path': os.path.join(dirpath, 'static'),
            'template_path': os.path.join(dirpath, 'static'),
            'cookie_secret': base64.b64encode(os.urandom(32)).decode(),
            'xsrf_cookies': False,
            'login_url': '/login'
        }
        super(BotApplication, self).__init__(handlers, **settings)


@coroutine
def recvMessage():
    """队列处理消息
    """
    while 1:
        nxt = sleep(options.delay)
        try:
            message = yield MessageInQueue.get()
            # 解析数据整理格式
            message = Interface._getMsgInfo(message)
            print(message)
        except Exception as e:
            log.exception(e)
        yield nxt


@coroutine
def sendMessage():
    """队列发送消息
    """
    while 1:
        nxt = sleep(options.delay)
        try:
            message = yield MessageOutQueue.get()
        except Exception as e:
            log.exception(e)
        yield nxt


@coroutine
def setupQQLight():
    while 1:
        try:
            BotInterface.QQLightWs = yield websocket_connect(HTTPRequest('ws://{}:{}/'.format(options.qlhost, options.qlport), validate_cert=False))
            while 1:
                nxt = sleep(options.delay)
                message = yield BotInterface.QQLightWs.read_message()
                try:
                    message = json.loads(
                        to_basestring(message), object_hook=DottedDict)
                    yield MessageInQueue.put(message)
                except Exception as e:
                    log.exception(e)
                yield nxt
        except Exception as e:
            log.exception(e)

        # 300秒后重连
        log.info('reconnect qqlight bot after 300s')
        yield sleep(300)


def main():
    # 初始化日志和异常捕捉
    colorama.init()
    # enable_pretty_logging()
    options.logging = 'info'

    log.info('listen on %s:%s', options.host, options.port)
    log.info('cq bot: %s:%s', options.cqhost, options.cqport)
    log.info('ql bot: %s:%s', options.qlhost, options.qlport)
    log.info('qy bot: %s:%s', options.qyhost, options.qyport)

    # 创建本地web服务
    server = HTTPServer(BotApplication())
    server.listen(options.port, options.host)

    loop = IOLoop.current()
    # 队列处理消息
    loop.spawn_callback(recvMessage)
    # 队列发送消息
    loop.spawn_callback(sendMessage)
    # qqlight
    loop.spawn_callback(setupQQLight)
    loop.start()


if __name__ == '__main__':
    main()
