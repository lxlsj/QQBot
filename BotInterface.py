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
    Cqp, Mpq, Amanda, CleverQQ, QQLight, Qy = range(6)

    def formatAt(self, qq=None):
        """格式化at消息
        :param qq:        qq号或者None代表所有人
        """
        return '[CQ:at,qq={0}]'.format(qq or 'all') \
            if self == Interface.Cqp else '[@{0}]'.format(qq or '0') \
            if self == Interface.Mpq else '[IR:at={0}]'.format(qq or '全体人员') \
            if self == Interface.CleverQQ else '[QQ:at={0}]'.format(qq or 'all') \
            if self == Interface.QQLight else '[@{0}]'.format(qq or 'all') \
            if self == Interface.Qy else ''

    def formatFace(self, fid):
        """格式化表情
        :param fid:        表情id
        """
        return ('[CQ:face,id={0}]'
                if self == Interface.Cqp else 'Face{0}.gif'
                if self == Interface.Mpq else '[Face{0}.gif]'
                if self == Interface.CleverQQ else '[QQ:face={0}]'
                if self == Interface.QQLight else '[LQ:face,id={0}]'
                if self == Interface.Qy else ''
                ).format(fid)

    def formatImg(self, image):
        """格式化图片
        :param image:        图片
        """
        if self == Interface.Cqp:
            # 直接无视,理由: Air不支持，文档说明只支持酷Q目录的data\image\下
            # [CQ:image,file=1.jpg]
            return ''
        if self == Interface.Mpq:
            # {6A86C083-927A-BB63-720A-93FAA345A3FC}.jpg
            return image
        if self == Interface.CleverQQ:
            # 腾讯默认代码[IR:pic={XXXXXXXX-XXXXX-XXXX-XXXX-XXXXXXXXXX}.jpg] （GUID格式）
            return '[IR:pic={0}]'.format(image)
        if self == Interface.QQLight:
            # 本地绝对路径图片、网络图片链接、GUID（通过上传图片获得）
            # [QQ:pic=本地图片绝对路径]
            # [QQ:pic=网络图片链接]
            # [QQ:pic=GUID]
            if os.path.exists(image):
                image = os.path.abspath(image).replace('\\', '/')
            return '[QQ:pic={0}]'.format(image)
        if self == Interface.Qy:
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

    def filterMsg(self, message):
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
        :param url:                待提交的json格式数据
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
        if self == Interface.Qy or self == Interface.Cqp:
            message = message.replace('&', '&amp;').replace(
                '[', '&#91;').replace(']', '&#93;').replace(',', '&#44;')
        return message

    def unescape(self, message):
        """文本反转义
        :param message:
        """
        if self == Interface.Qy or self == Interface.Cqp:
            message = message.replace('&#44;', ',').replace(
                '&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')
        return message

    @coroutine
    def sendMsg(self, message):
        """发送消息
        :param message:
        """
        url = 'http://{0}:{1}/api/v1/{2}/Api_SendMsg'.format(
            options.ahost, options.aport, self.name,
            'Api_SendMsg' if self != Interface.Cqp else 'CQ_sendPrivateMsg'
            if message.MessageType == 21 else 'CQ_sendGroupMsg'
            if message.MessageType == 2 else 'CQ_sendDiscussMsg'
            if message.MessageType == 4 else '')
        if not url.endswith('Msg'):
            logging.warning('url({0}) is bad'.format(url))
            return
        QQInt = int(message.QQ) if message.QQ else 0
        QQStr = message.QQ if message.QQ else ''
        GroupInt = int(message.Group) if message.Group else 0
        GroupStr = message.Group if message.Group else ''
        data = {
            # 酷Q
            'qqid': QQInt,
            '群号': GroupInt,
            '讨论组号': GroupInt,
            'msg': message.Message,
            # CleverQQ, Mpq
            '响应的QQ': message.RQQ,  # 自己
            '信息类型': message.MessageType,
            '参考子类型': 0,  # 无特殊说明情况下留空或填零
            '收信群_讨论组': GroupStr,
            '收信对象群_讨论组': GroupStr,
            '收信对象': QQStr,
            '收信QQ': QQStr,
            '气泡ID': -1,      # CleverQQ 气泡 -1随机
            # QQLight
            '类型': message.MessageType,
            '群组': GroupStr,
            'qQ号': QQStr,
            '内容': message.Message,
        }
        code, data = yield self.post(url, data=data)
        logging.debug(
            'sendMsg return [code: {0}, data: {1}]'.format(code, data))

    @classmethod
    def getMsgInfo(cls, message):
        """提取各大平台机器人的json数据中的有效字段并整合
        :param cls:
        :param message:
        :return: {
            'Group': 'QQ群',            # 发送的QQ群或者为空
            'QQ': '发送人QQ',            # 消息发送人QQ
            'RQQ': '机器人QQ'            # 机器人QQ
            'RawMessage': '原始消息',      # 原始消息
            'Message': '过滤后的消息',       # 过滤后的消息
            'Ats': [],                  # 被艾特人列表
            'MessageId': '消息ID',      # 消息ID（撤回用）或者为空
            'MessageType': 1,          # 消息类型
            'Interface':  < Interface.QQLight: 4 >  # 统一封装接口
        }
        """
        # 文本消息
        RawMessage = message.Message
        if RawMessage is None:
            return None
        # 消息类型
        MessageType = message.EventType or message.Type
        # 0-酷Q, 1-MPQ, 2-Amanda, 3-CleverQQ, 4-QQLight
        # 接口实例
        _Interface = cls(message.Platform)
        return DottedDict(
            # 0-酷Q, 1-MPQ, 2-Amanda, 3-CleverQQ, 4-QQLight
            Interface=_Interface,
            # 发送人
            QQ=message.EventOperator or message.Fromqq,
            # 机器人QQ
            RQQ=message.ReceiverQq or '',
            # 群号
            Group=message.FromNum or message.Fromgroup,
            # 原始文本消息
            RawMessage=RawMessage.strip(),
            # 过滤后的纯文本消息
            Message=_Interface.unescape(
                _Interface.filterMsg(RawMessage)).strip(),
            # 消息ID（MPQ没有）
            MessageId=message.MessageId,
            # 消息类型
            MessageType=MessageType,
            # 被艾特的人列表
            Ats=_Interface.getAts(RawMessage)
        )


if __name__ == '__main__':
    for i in range(len(Interface)):
        i = Interface(i)
        print(i.name, i.value, 'formatFace(1):', i.formatFace(1))

    print()

    for i in range(len(Interface)):
        i = Interface(i)
        print(i.name, i.value, 'formatAt:',
              i.formatAt('892768447'), i.formatAt())
