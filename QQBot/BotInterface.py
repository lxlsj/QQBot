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
from enum import Enum
import json
import logging
import os
import re
from urllib.parse import urlencode

from tornado.escape import to_basestring
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options
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

# QQLight的Websocket对象
QQLightWs = None


class DottedDict(dict):

    def __getattr__(self, attr):
        try:
            value = self[attr]
            if isinstance(value, dict):
                return DottedDict(value)
            return value
        except KeyError as e:
            logging.debug(e)
            return DottedDict()

    __setattr__ = dict.__setitem__

    __delattr__ = dict.__delitem__


class MessageType(Enum):
    """消息类型
    """
    PRIVATE, GROUP, OTHER = range(3)


class EventType(Enum):

    """
    MESSAGE:             收到消息
    FRIENDREQUEST:       好友请求
    FRIENDCHANGE:        好友变动
    GROUPMEMBERINCREASE: 群成员增加
    GROUPMEMBERDECREASE: 群成员减少
    ADMINCHANGE:         群管理员变动
    GROUPREQUEST:        加群请求
    RECEIVEMONEY:        收款
    GROUPBAN:            群禁言
    OTHER:               其它事件
    """
    MESSAGE, FRIENDREQUEST, FRIENDCHANGE, GROUPMEMBERINCREASE,\
        GROUPMEMBERDECREASE, ADMINCHANGE, GROUPREQUEST, RECEIVEMONEY,\
        GROUPBAN, OTHER = range(10)


class Interface(Enum):
    CQ, QY, QL = range(3)

    def formatAt(self, qq=None):
        """格式化at消息
        :param QQ:        QQ号或者None代表所有人
        """
        return '[CQ:at,qq={0}]'.format(qq or 'all') if self == Interface.CQ \
            else '[@{0}]'.format(qq or 'all') if self == Interface.QY \
            else '[@{0}]'.format(qq or '0') if self == Interface.QL else ''

    def getAts(self, message):
        """提取被艾特的人
        :param message:    原始消息
        """
        return re.findall('\[(?:QQ:at=|IR:at=|CQ:at,qq=|@)(\d{5,20})\]', message)

    def formatFace(self, fid):
        """格式化表情
        :param fid:        表情id
        """
        return ('[CQ:face,id={0}]' if self == Interface.CQ
                else '[LQ:face,id={0}]' if self == Interface.QY
                else '[QQ:face={0}]' if self == Interface.QL else ''
                ).format(fid)

    def formatImg(self, image):
        """格式化图片
        :param image:        图片
        """
        if self == Interface.CQ:
            # Air不支持，文档说明只支持酷Q目录的data\image\下
            return '[CQ:image,file={0}]'.format(image)
        if self == Interface.QL:
            # 本地绝对路径图片、网络图片链接、GUID（通过上传图片获得）
            # [QQ:pic=本地图片绝对路径]
            # [QQ:pic=网络图片链接]
            # [QQ:pic=GUID]
            if os.path.exists(image):
                image = os.path.abspath(image).replace('\\', '/')
            return '[QQ:pic={0}]'.format(image)
        if self == Interface.QY:
            # 本地绝对路径图片、网络图片链接
            if image.lower().startswith('http'):
                return '[LQ:image,urls={}]'.format(image)
            if os.path.exists(image):
                return '[LQ:image,path={}]'.format(os.path.abspath(image).replace('\\', '/'))

    def getImgs(self, message):
        """提取图片url
        :param message:    原始消息
        """
        return re.findall('\[(?:CQ:image.*?,url|QQ:pic|LQ:image.*?,urls)=(.*?)\]', message)

    def filterMessage(self, message):
        """过滤消息内容去掉艾特、表情、图片、链接等信息
        :param message:    原始消息
        """
        message = re.sub('(\[QQ:.*?\])|'
                         '(\[IR:.*?\])|'
                         '(\[CQ:.*?\])|'
                         '(\[LQ:.*?\])|'
                         '(\[Face.*?gif\])|'
                         '(\[@.*?\])|'
                         '(Face.*?gif)|'
                         '(\{.*?\}(\.jpg|\.png|\.gif))', '', message)
        return re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', message)

    @coroutine
    def get(self, url, retJson=False, retBinary=False, **kwargs):
        """http get请求数据
        :param url:                网址
        :param json:               返回json
        :param binary:             返回原始数据
        """
        client = AsyncHTTPClient()
        headers = DefaultHeaders.copy().update(kwargs.pop('headers', {}))
        resp = yield client.fetch(url, method='GET', headers=headers, max_redirects=3, **kwargs)
        if not resp.body:
            return resp.code, ''
        if retBinary:
            return resp.code, resp.body
        if retJson:
            try:
                return resp.code, json.loads(to_basestring(resp.body.decode()), object_hook=DottedDict)
            except:
                return resp.code, DottedDict()
        return resp.code, resp.body.decode()

    @coroutine
    def post(self, url, body=None, data=None, retJson=False, retBinary=False, **kwargs):
        """http post请求数据
        :param url:                网址
        :param body:               待提交的字符串内容
        :param data:               待提交的json格式数据
        :param json:               返回json
        :param binary:             返回原始数据
        """
        client = AsyncHTTPClient()
        headers = DefaultHeaders.copy()
        headers.update(kwargs.pop('headers', {}))
        if data:
            headers['Content-Type'] = 'application/json; charset=utf-8'
            body = json.dumps(data)
        elif body:
            body = urlencode(body) if body else ''
        else:
            body = ''
        resp = yield client.fetch(url, method='POST', body=body, headers=headers, max_redirects=3, **kwargs)
        if not resp.body:
            return resp.code, ''
        if retBinary:
            return resp.code, resp.body
        if retJson:
            try:
                return resp.code, json.loads(to_basestring(resp.body.decode()), object_hook=DottedDict)
            except:
                return resp.code, DottedDict()
        return resp.code, resp.body.decode()

    def escape(self, message):
        """文本转义
        :param message:
        """
        if self == Interface.QY or self == Interface.CQ:
            message = message.replace('&', '&amp;').replace(
                '[', '&#91;').replace(']', '&#93;').replace(',', '&#44;')
        return message

    def unescape(self, message):
        """文本反转义
        :param message:
        """
        if self == Interface.QY or self == Interface.CQ:
            message = message.replace('&#44;', ',').replace(
                '&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')
        return message

    def _getEventType(self, message):
        bot_op_type = -1
        bot_event = -1
        if self == Interface.QL:
            bot_event = getattr(EventType, message.event.upper())
        elif self == Interface.CQ:
            if message.post_type == 'message':
                bot_event = EventType.MESSAGE
            elif message.post_type == 'notice':
                notice_type = message.notice_type
                sub_type = message.sub_type
                bot_event = EventType.OTHER
                if notice_type == 'group_admin':  # 群管理员变动
                    bot_event = EventType.ADMINCHANGE
                    # 1=成为管理、2=被解除管理
                    bot_op_type = 1 if sub_type == 'set' else 2 if sub_type == 'unset' else -1
                elif notice_type == 'group_decrease':  # 群成员减少
                    bot_event = EventType.GROUPMEMBERDECREASE
                    # 1=主动退群、2=被管理员踢出、3=登录号被踢
                    bot_op_type = 1 if sub_type == 'leave' else 2 if sub_type == 'kick' else 3 if sub_type == 'kick_me' else -1
                elif notice_type == 'group_increase':  # 群成员增加
                    bot_event = EventType.GROUPMEMBERINCREASE
                    # 1=主动加群、2=被管理员邀请
                    bot_op_type = 1 if sub_type == 'approve' else 2 if sub_type == 'invite' else -1
                elif notice_type == 'group_ban':       # 群禁言
                    bot_event = EventType.GROUPBAN
                    # 1=禁言、2=解除禁言
                    bot_op_type = 1 if sub_type == 'ban' else 2 if sub_type == 'lift_ban' else -1
                elif notice_type == 'friend_add':      # 好友添加
                    bot_event = EventType.FRIENDCHANGE
            elif message.post_type == 'request':
                request_type = message.request_type
                bot_event = EventType.OTHER
                if request_type == 'friend':      # 加好友请求
                    bot_event = EventType.FRIENDREQUEST
                elif request_type == 'group':     # 加群请求
                    bot_event = EventType.GROUPREQUEST
                    # 1=主动加群、2=被邀请进群、3=机器人被邀请进群
                    bot_op_type = 1 if sub_type == 'add' else 2 if sub_type == 'invite' else 3
        elif self == Interface.QY:
            eventType = message.eventType
            if eventType == 101:
                # 好友请求
                bot_event = EventType.FRIENDREQUEST
            elif eventType in (100, 102, 104):
                # 好友变动
                bot_event = EventType.FRIENDCHANGE
            elif eventType in (215, 219, 212):
                # 群成员增加
                bot_event = EventType.GROUPMEMBERINCREASE
                # 1=主动加群、2=被管理员邀请
                bot_op_type = 1 if eventType == 212 else 2 if eventType == 215 else 3 if eventType == 219 else -1
            elif eventType in (201, 202):
                # 群成员减少
                bot_event = EventType.GROUPMEMBERDECREASE
                bot_op_type = str(eventType)[-1]
            elif eventType in (210, 211):
                # 群管理员变动
                bot_event = EventType.ADMINCHANGE
                bot_op_type = 1 if eventType == 210 else 2 if eventType == 211 else -1
            elif eventType in (213, 214):
                # 加群请求
                bot_event = EventType.GROUPREQUEST
                bot_op_type = 1 if eventType == 213 else 2 if eventType == 214 else 3
            elif eventType == 6:
                # 收款
                bot_event = EventType.RECEIVEMONEY
            elif eventType in (205, 206):
                # 禁言
                bot_event = EventType.GROUPBAN
                # 1=禁言、2=解除禁言
                bot_op_type = 1 if eventType == 205 else 2 if eventType == 206 else -1
        return {
            'bot_event': bot_event,
            'bot_op_type': bot_op_type,
        }

    @coroutine
    def sendMsg(self, message):
        """发送消息
        :param message:
        """
        if message.interface == Interface.QL:
            return
        if message.interface == Interface.CQ:
            url = 'http://127.0.0.1:{0}'.format(options.cqport)
        elif message.interface == Interface.QY:
            url = 'http://127.0.0.1:{0}'.format(options.qyport)
        code, data = yield self.post(url, data=message)
        logging.debug(
            'sendMsg return [code: {0}, data: {1}]'.format(code, data))

    @classmethod
    def _getMsgInfo(cls, message):
        """提取各大平台机器人的json数据中的有效字段并整合
        :param cls:
        :param message:
        :return: 
        """

        # 0-CQ, 1-QY, 2-QL
        # 接口实例
        bot_interface = cls(Interface.CQ if message.post_type
                            else Interface.QY if message.eventType
                            else Interface.QL if message.params
                            else None)
        if not bot_interface:
            return None

        # 原始消息
        bot_raw_message = message.message or message.duration or \
            message.comment or message.content or \
            message.params.content or message.params.message or \
            message.params.amount or ''
        if not bot_raw_message:
            return None

        # 消息类型
        message_type = str(
            message.message_type or message.eventType or message.params.type)
        if message_type:
            if message_type == 'group' or message_type in '2345':
                bot_msg_type = MessageType.GROUP
            elif message_type == 'private' or message_type == '1':
                bot_msg_type = MessageType.PRIVATE
            else:
                bot_msg_type = MessageType.OTHER

        # 在原来的基础上增加新字段
        message.update({
            # 0-CQ, 1-QY, 2-QL
            'bot_interface': bot_interface,
            # 发送人
            'bot_user_id': message.user_id or message.fromQQ or message.params.qq or '',
            # 机器人QQ
            'bot_self_id': message.self_id or message.qq or '',
            # 操作者QQ
            'bot_op_id': message.operator_id or message.fromQQ or message.params.operator or '',
            # 序列号(处理某些请求用到)
            'bot_seq': message.flag or message.params.seq or '',
            # 群号
            'bot_group': message.group_id or message.fromID or message.params.group or '',
            # 原始文本消息
            'bot_raw_message': bot_raw_message.strip(),
            # 过滤后的纯文本消息
            'bot_msg': bot_interface.unescape(
                bot_interface.filterMessage(bot_raw_message)).strip(),
            # 消息ID
            'bot_msgid': message.message_id or message.msgID or message.params.msgid or '',
            # 消息类型
            'bot_msg_type': bot_msg_type,
            # 被艾特的人列表
            'bot_ats': bot_interface.getAts(bot_raw_message),
            # 图片
            'bot_imgs': bot_interface.getImgs(bot_raw_message)
        })
        message.update(bot_interface._getEventType(message))
        return DottedDict(message)


if __name__ == '__main__':

    for i in range(len(Interface)):
        i = Interface(i)
        print(i.name, i.value,
              'formatFace(1):', i.formatFace(1))

    print()

    for i in range(len(Interface)):
        i = Interface(i)
        print(i.name, i.value, 'formatAt:',
              i.formatAt('892768447'), i.formatAt())
