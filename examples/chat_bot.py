#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# @AUTHOR: Rabbir
# @FILE: /root/Github/steampy/examples/chat_bot.py
# @DATE: 2021/01/27 Wed
# @TIME: 13:35:51
#
# @DESCRIPTION: todo...


import time
# 切换路径到父级
import sys
sys.path.append("..")
from steampy.client import SteamClient
from examples import bot_info


# API KEY
api_key = bot_info.get_api_key()
# Steam 手机令牌路径
steamguard_path = bot_info.get_steamguard_path()
# Steam 用户名
username = bot_info.get_username()
# Steam 密码
password = bot_info.get_password()


"""
@description: 判断是否所有用户信息都已经填写
-------
@param:
-------
@return: <bool>
"""
def are_credentials_filled() -> bool:
    return (api_key != '' 
                and steamguard_path != ''
                and username != ''
                and password != '')

"""
@description: 启动聊天机器人的主方法
-------
@param:
-------
@return:
"""
def main():
    print('Steam 聊天机器人启动...')
    if not are_credentials_filled():
        print('你需要按要求填写所有信息！')
        print('Steam 聊天机器人结束。')
        return
    client = SteamClient(api_key)
    client.login(username, password, steamguard_path)
    print('机器人登录成功！已设定为每 10 秒轮询一次聊天列表。')
    client.chat._login()
    while True:
        time.sleep(10)
        messages = client.chat.fetch_messages()['received']
        for message in messages:
            client.chat.send_message(message['partner'],
                                     "Got your message: "+message['message'])


"""
@description: 单体测试
-------
@param:
-------
@return:
"""
if __name__ == "__main__":
    # 以脚本形式运行
    main()
