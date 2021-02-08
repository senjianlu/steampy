#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# @AUTHOR: Rabbir
# @FILE: /root/Github/steampy/steampy/guard.py
# @DATE: 2021/02/08 Mon
# @TIME: 17:44:31
#
# @DESCRIPTION: Steam 桌面令牌 SDA 方法集合模块


import base64
import hmac
import json
import struct
import time
import os
from hashlib import sha1


"""
@description: 加载 Steam 令牌
-------
@param:
-------
@return:
"""
def load_steam_guard(steam_guard: str) -> dict:
    if os.path.isfile(steam_guard):
        with open(steam_guard, "r") as f:
            return json.loads(f.read())
    else:
        return json.loads(steam_guard)

"""
@description: 生成登录用令牌码
-------
@param:
-------
@return:
"""
def generate_one_time_code(shared_secret: str, timestamp: int=None) -> str:
    if timestamp is None:
        timestamp = int(time.time())
    # pack as Big endian, uint64
    time_buffer = struct.pack(">Q", timestamp // 30)
    time_hmac = hmac.new(
        base64.b64decode(shared_secret), time_buffer, digestmod=sha1).digest()
    begin = ord(time_hmac[19:20]) & 0xf
    # unpack as Big endian uint32
    full_code = struct.unpack(
        ">I", time_hmac[begin:begin + 4])[0] & 0x7fffffff
    chars = "23456789BCDFGHJKMNPQRTVWXY"
    code = ""
    # 拼凑
    for _ in range(5):
        full_code, i = divmod(full_code, len(chars))
        code += chars[i]
    return code

"""
@description: 生成交易确认码
-------
@param:
-------
@return:
"""
def generate_confirmation_key(identity_secret: str,
                              tag: str,
                              timestamp: int=int(time.time())) -> bytes:
    buffer = struct.pack(">Q", timestamp) + tag.encode("ascii")
    confirmation_key = base64.b64encode(
        hmac.new(base64.b64decode(identity_secret),
                 buffer,
                 digestmod=sha1).digest())
    return confirmation_key

"""
@description: 生成设备 ID
-------
@param:
-------
@return:
"""
def generate_device_id(steam_id: str) -> str:
    hexed_steam_id = sha1(steam_id.encode("ascii")).hexdigest()
    return "android:" + "-".join([hexed_steam_id[:8],
                                  hexed_steam_id[8:12],
                                  hexed_steam_id[12:16],
                                  hexed_steam_id[16:20],
                                  hexed_steam_id[20:32]])
