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

    @classmethod
    def getMsgInfo(cls, message):
        """提取各大平台机器人的json数据中的有效字段并整合
        :param cls:
        :param message:
        """
        return DottedDict(
            # 0-酷Q, 1-MPQ, 2-Amanda, 3-CleverQQ, 4-QQLight
            Platform=message.Platform,
            # 发送人
            QQ=message.EventOperator or message.Fromqq,
            # 群号
            Group=message.FromNum or message.Fromgroup,
            # 文本消息
            Message=message.Message,
            # 消息ID（MPQ没有）
            MessageId=message.MessageId,
            # 1-私聊, 2-群聊, 4-讨论组
            MessageType=message.EventType or message.Type
        )
