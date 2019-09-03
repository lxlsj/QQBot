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


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019 Irony'
__Version__ = 1.0


@coroutine
def _send_message(message):
    pass


@coroutine
def _recv_message(message):
    """
    {
        'Type': 2,                    # 1私聊,2群聊
        'Message': '消息', 
        'MessageId': '消息ID', 
        'Fromgroup': 'QQ群', 
        'CreateTime': '时间', 
        'Fromqq': '发送人', 
        'Platform': 4, 
        'TypeCode': 
        'GetNewMsg'
    }
    QQLight：
        # 图片 [QQ:pic=4706bf6b-f6b8-f4b6-dcc3-1bee23b39c14.jpg]
        # 表情 [QQ:face=178]
    """
    Platform = message.Platform     # 0-酷Q, 1-MPQ, 2-Amanda, 3-CleverQQ, 4-QQLight
    QQ = message.EventOperator or message.Fromqq        # 发送人
    Group = message.FromNum or message.Fromgroup       # 群号
    Message = message.Message                           # 文本消息
    MessageId = message.MessageId                       # 消息ID（MPQ没有）
    MessageType = message.EventType or message.Type
    print(Platform, QQ, Group, Message, MessageId, MessageType)
