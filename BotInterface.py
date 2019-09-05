#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年9月4日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: BotInterface
@description: 统一接口
"""
from enum import Enum
import logging
import re


__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019'


class DottedDict(dict):
    # 用于实现通过.方式直接访问字典中的数据

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as e:
            logging.debug(e)
            return None

    __setattr__ = dict.__setitem__

    __delattr__ = dict.__delitem__


class Interface(Enum):
    """提供统一接口URL和参数"""
    Cqp, Mpq, Amanda, CleverQQ, QQLight = range(5)

    def formatShortCode(self, key, value):
        """封装短码
        :param key:            键,如：face,emoji,bface,sface,image,record
        :param value:          值
        """
        if self == Interface.Cqp:
            if key == 'shake':
                return '[CQ:shake]'
            return '[CQ:{0},{1}={2}]'.format(
                key, 'id' if key in (
                    'face', 'emoji', 'bface', 'sface') else 'file'
                if key == 'image' else 'qq' if key == 'at' else 'type'
                if key in ('rps', 'dice') else 'ignore' if key == 'anonymous' else '', value)
        elif self == Interface.Mpq:
            pass
        elif self == Interface.CleverQQ:
            pass
        elif self == Interface.QQLight:
            pass

    def getAts(self, message):
        """提取被艾特的人
        :param message:    原始消息
        """
        return re.findall('\[(?:QQ:at=|IR:at=|CQ:at,qq=|@)(\d+)\]', message)

    def filterMsg(self, message):
        """过滤消息内容去掉艾特、表情、图片、链接等信息
        :param message:    原始消息
        """
        message = re.sub('(\[QQ:.*?\])|'
                         '(\[IR:.*?\])|'
                         '(\[CQ:.*?\])|'
                         '(\[Face.*?gif\])|'
                         '(\[@\d+\])|'
                         '(Face.*?gif)|'
                         '(\{.*?\}(\.jpg|\.png|\.gif))', '', message)
        return re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', message)

    @classmethod
    def getMsgInfo(cls, message):
        """提取各大平台机器人的json数据中的有效字段并整合
        :param cls:
        :param message:
        """
        # 0-酷Q, 1-MPQ, 2-Amanda, 3-CleverQQ, 4-QQLight
        Platform = message.Platform
        # 接口实例
        _Interface = cls(Platform)
        # 文本消息
        RawMessage = message.Message
        # 1-私聊, 2-群聊, 4-讨论组
        MessageType = message.EventType or message.Type
        return DottedDict(
            # 0-酷Q, 1-MPQ, 2-Amanda, 3-CleverQQ, 4-QQLight
            Platform=Platform,
            # 发送人
            QQ=message.EventOperator or message.Fromqq,
            # 群号
            Group=message.FromNum or message.Fromgroup,
            # 原始文本消息
            RawMessage=RawMessage,
            # 过滤后的纯文本消息
            Message=Interface.filterMsg(RawMessage),
            # 消息ID（MPQ没有）
            MessageId=message.MessageId,
            # 1-私聊, 2-群聊, 4-讨论组
            MessageType=MessageType,
            # 是否是私聊
            IsPrivate=MessageType == 1,
            # 是否群聊
            isGroup=(MessageType == 2 or MessageType == 4),
            # 被艾特的人列表
            Ats=_Interface.getAts(RawMessage),
            # 接口实例
            Interface=_Interface
        )
