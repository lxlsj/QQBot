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
from urllib.parse import urlencode
import json
import logging
import os
import re

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


class DottedDict(dict):

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as e:
            logging.debug(e)
            return None

    __setattr__ = dict.__setitem__

    __delattr__ = dict.__delitem__


class MessageType(Enum):
    """消息类型
    """
    PRIVATE, GROUP, SYSTEM, OTHER = range(4)


class Interface(Enum):
    CQ, QY, QQLIGHT = range(3)

    def formatAt(self, qq=None):
        """格式化at消息
        :param QQ:        QQ号或者None代表所有人
        """
        return '[CQ:at,qq={0}]'.format(qq or 'all') if self == Interface.CQ \
            else '[@{0}]'.format(qq or 'all') if self == Interface.QY \
            else '[@{0}]'.format(qq or '0') if self == Interface.QQLIGHT else ''

    def formatFace(self, fid):
        """格式化表情
        :param fid:        表情id
        """
        return ('[CQ:face,id={0}]' if self == Interface.CQ
                else '[LQ:face,id={0}]' if self == Interface.QY
                else '[QQ:face={0}]' if self == Interface.QQLIGHT else ''
                ).format(fid)

    def formatImg(self, image):
        """格式化图片
        :param image:        图片
        """
        if self == Interface.CQ:
            # Air不支持，文档说明只支持酷Q目录的data\image\下
            return '[CQ:image,file={0}]'.format(image)
        if self == Interface.QQLIGHT:
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

    def getAts(self, message):
        """提取被艾特的人
        :param message:    原始消息
        """
        return re.findall('\[(?:QQ:at=|IR:at=|CQ:at,qq=|@)(\d{5,20})\]', message)

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

    @coroutine
    def sendMsg(self, message):
        """发送消息
        :param message:
        """
        if message.interface == Interface.QQLIGHT:
            return
        if message.interface == Interface.CQ:
            url = 'http://127.0.0.1:{0}'.format(options.cqport)
        elif message.interface == Interface.QY:
            url = 'http://127.0.0.1:{0}'.format(options.qyport)
        code, data = yield self.post(url, data=message)
        logging.debug(
            'sendMsg return [code: {0}, data: {1}]'.format(code, data))

    @classmethod
    def getMsgInfo(cls, message):
        """提取各大平台机器人的json数据中的有效字段并整合
        :param cls:
        :param message:
        """

        # 原始消息
        rawMessage = message.message or message.content
        if rawMessage is None:
            return None

        # 消息类型
        message_type = message.message_type or message.eventType
        if message_type:
            if message_type == 'group' or message_type in '2345':
                msgType = MessageType.GROUP
            elif message_type == 'private' or message_type == '1':
                msgType = MessageType.PRIVATE
            else:
                msgType = MessageType.OTHER

        # 0-CQ, 1-QY, 2-QQLIGHT
        # 接口实例
        interface = cls(Interface.CQ if message.raw_message
                        else Interface.QY if message.eventType
                        else Interface.QQLIGHT)

        message.update({
            # 0-CQ, 1-QY, 2-QQLIGHT
            'interface': interface,
            # 发送人
            'fqq': message.user_id or message.fromQQ or '',
            # 机器人QQ
            'rqq': message.self_id or message.qq or '',
            # 群号
            'group': message.group_id or message.fromID or '',
            # 原始文本消息
            'raw': rawMessage.strip(),
            # 过滤后的纯文本消息
            'msg': interface.unescape(
                interface.filterMessage(rawMessage)).strip(),
            # 消息ID
            'msgid': message.message_id or message.msgID or '',
            # 消息类型
            'msgType': msgType,
            # 被艾特的人列表
            'ats': interface.getAts(rawMessage)
        })
        return DottedDict(message)


if __name__ == '__main__':

    for i in range(len(Interface)):
        i = Interface(i)
        print(i.name, i.value, 'formatFace(1):', i.formatFace(1))

    print()

    for i in range(len(Interface)):
        i = Interface(i)
        print(i.name, i.value, 'formatAt:',
              i.formatAt('892768447'), i.formatAt())
