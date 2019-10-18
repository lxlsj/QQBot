#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年9月2日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: BotServer
@description: 
"""
import logging

import colorama
from tornado.gen import coroutine, sleep
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define
from tornado.options import options
from tornado.web import Application

from BaseHandler import MahuaHandler, IndexHandler


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019 Irony'
__Version__ = 1.0

define('host', default='127.0.0.1',
       metavar='127.0.0.1 or 0.0.0.0 or other ip', help='PY机器人地址')
define('cqport', type=int, default=65322, help='CQA端口: 65322')
define('qlport', type=int, default=65323, help='QQLight端口: 65323')
define('qyport', type=int, default=65324, help='QY端口: 65324')


class BotApplication(Application):

    def __init__(self, *args, **kwargs):  # @UnusedVariable
        handlers = [
            (r'/api/ReceiveMahuaOutput', MahuaHandler),
            (r'/.*', IndexHandler)
        ]
        settings = {'debug': False}
        super(BotApplication, self).__init__(handlers, **settings)


@coroutine
def recvMessage(msgHandler):
    """队列处理消息
    """
    while 1:
        nxt = sleep(0.01)
        try:
            yield msgHandler._recv_message()
        except Exception as e:
            logging.exception(e)
        yield nxt


@coroutine
def sendMessage(msgHandler):
    """队列发送消息
    """
    while 1:
        nxt = sleep(0.01)
        try:
            yield msgHandler._send_message()
        except Exception as e:
            logging.exception(e)
        yield nxt


def main(msgHandler):
    # 初始化日志和异常捕捉
    colorama.init()
    # enable_pretty_logging()

    # 解析命令行参数
    options.log_file_prefix = options.log_file_prefix or 'log.log'
    options.log_to_stderr = options.log_to_stderr or True
    options.parse_command_line()

    logging.info('host: {}'.format(options.host))
    logging.info('cqport: {}'.format(options.cqport))
    logging.info('qlport: {}'.format(options.qlport))
    logging.info('qyport: {}'.format(options.qyport))

    # 创建本地web服务
    cqserver = HTTPServer(BotApplication())
    cqserver.listen(options.cqport, options.host)
    qlserver = HTTPServer(BotApplication())
    qlserver.listen(options.qlport, options.host)
    qyserver = HTTPServer(BotApplication())
    qyserver.listen(options.qyport, options.host)
    
    loop = IOLoop.current()
    # 队列处理消息
    loop.spawn_callback(recvMessage, msgHandler)
    # 队列发送消息
    loop.spawn_callback(sendMessage, msgHandler)
    loop.start()


if __name__ == '__main__':
    import sys
    sys.argv.append('--host=192.168.1.2')
    sys.argv.append('--qlport=65533')
    options.parse_command_line()
    print(options.host)
    print(options.cqport)
    print(options.qlport)
    print(options.qyport)
