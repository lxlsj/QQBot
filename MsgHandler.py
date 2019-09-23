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

import BotInterface


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019 Irony'
__Version__ = 1.0


class MsgHandler:

    @coroutine
    def _send_message(self):
        """发送队列消息
        """
        message = yield BotInterface.MessageOutQueue.get()
        yield message.Interface.sendMsg(message)

    @coroutine
    def _recv_message(self):
        """接收队列消息
        """
        message = yield BotInterface.MessageInQueue.get()
        message = BotInterface.Interface.getMsgInfo(message)
        if not message or not message.RawMessage:
            return
        if 0 < message.MessageType < 8:
            # 私聊或者群消息
            message = yield self.onMessage(message)
            if not message:
                return
            BotInterface.MessageOutQueue.put(message)

    @coroutine
    def onMessage(self, message):
        """处理消息
        :param message: {
                'Group': 'QQ群',            # 发送的QQ群或者为空
                'QQ': '发送人QQ',            # 消息发送人QQ
                'RQQ': '机器人QQ'            # 机器人QQ
                'RawMessage': '原始消息',      # 原始消息
                'Message': '过滤后的消息',     # 过滤后的消息
                'Ats': [],                  # 被艾特人列表
                'MessageId': '消息ID',      # 消息ID（撤回用）或者为空
                'MessageType': 1,          # 消息类型
                'Interface':  < Interface.QQLight: 4 >  # 统一封装接口
            }
        :return: 返回message表示处理，返回None表示忽略
        """
