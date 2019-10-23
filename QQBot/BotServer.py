#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年10月23日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: QQBot.BotServer
@description: 
"""

import logging

from tornado.gen import coroutine, sleep
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define
from tornado.options import options
from tornado.web import Application
import colorama

from BaseHandler import MessageHandler, IndexHandler
from QQBot.BotHandlers import Handlers


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'
__Version__ = 1.0

define('host', default='127.0.0.1',
       metavar='127.0.0.1 or 0.0.0.0 or other ip', help='服务端绑定地址')
define('port', default=52610, help='服务端绑定端口')
define('delay', default=0.01, type=float, help='消息队列的休眠时间')
define('cqport', type=int, default=52611,
       help='酷Q 插件客户端监听端口, 需要在插件中自行设置\n见CQA/app/io.github.richardchien.coolqhttpapi/config.cfg')
define('qlport', type=int, default=52612,
       help='QQLight 插件客户端监听端口, 需要在插件中自行设置\n见QQLight/plugin/websocket.protocol/config.json')
define('qyport', type=int, default=52613,
       help='契约 插件客户端监听端口, 需要在插件中自行设置\n见QyBot/PC/plugin/com.tayuyu.http/你的QQ号.json文件\n新建你的QQ号.json内容为：{"port":"52613","urlList":["http://127.0.0.1:52610/message"]}')


class BotApplication(Application):

    def __init__(self, *args, **kwargs):
        # 扩展路由
        handlers = [h for h in Handlers if (
            h[0] != '/message' and h[0] != '.*')]
        handlers = handlers + [
            (r'/message', MessageHandler),
            (r'.*', IndexHandler)
        ]
        settings = {'debug': False}
        super(BotApplication, self).__init__(handlers, **settings)


@coroutine
def recvMessage(msgHandler):
    """队列处理消息
    """
    while 1:
        nxt = sleep(options.delay)
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
        nxt = sleep(options.delay)
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
    try:
        options.parse_config_file('config.cfg')
    except Exception as e:
        logging.warning(e)
    options.parse_command_line()

    logging.info('host: {}'.format(options.host))
    logging.info('port: {}'.format(options.port))
    logging.info('cqport: {}'.format(options.cqport))
    logging.info('qlport: {}'.format(options.qlport))
    logging.info('qyport: {}'.format(options.qyport))

    # 创建本地web服务
    server = HTTPServer(BotApplication())
    server.listen(options.port, options.host)

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
    try:
        options.parse_config_file('config.cfg')
    except:
        pass
    options.parse_command_line()
    print(options.host)
    print(options.port)
    print(options.cqport)
    print(options.qlport)
    print(options.qyport)
