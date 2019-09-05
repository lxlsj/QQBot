#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年9月6日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: BotExample
@description: 例子
"""
from tornado.gen import coroutine

from MsgHandler import MsgHandler
import BotServer


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'


class BotMsgHandler(MsgHandler):

    @coroutine
    def onMessage(self, message):
        """处理消息
        :param message: {
                'Group': 'QQ群',            # 发送的QQ群或者为空
                'QQ': '发送人QQ',            # 消息发送人QQ
                'RawMessage': '扯淡兔',      # 原始消息
                'Message': '扯淡兔',         # 过滤后的消息
                'Ats': [],                  # 被艾特人列表
                'MessageId': '消息ID',      # 消息ID（撤回用）或者为空
                'Interface':  < Interface.QQLight: 4 >  # 统一封装接口
            }
        :return: 返回message表示处理，返回None表示忽略
        """
        if message.QQ == '10000':
            # 系统消息，也有可能是撤回消息
            return
        # 这里只做复读机功能
        return message


if __name__ == '__main__':
    BotServer.main(BotMsgHandler())
